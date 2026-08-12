# Đặc tả hệ thống API thương mại điện tử

## 1. Mục tiêu

Xây dựng một hệ thống RESTful API production-ready cho website thương mại điện tử bằng Python và Django. Hệ thống phục vụ một Merchant duy nhất bán hàng hóa vật lý cho Customer đã đăng ký, bắt đầu vận hành tại Việt Nam nhưng có khả năng mở rộng có kiểm soát sang nhiều quốc gia, tiền tệ và ngôn ngữ.

Repository này chỉ chứa backend API. Storefront và Admin CMS là các ứng dụng frontend độc lập nằm ngoài repository và tích hợp qua OpenAPI contract.

### 1.1 Nguyên tắc sản phẩm

- Một Merchant duy nhất; không phải marketplace và không có Seller onboarding, commission hoặc payout.
- Customer bắt buộc đăng ký, xác minh email và đăng nhập trước khi checkout.
- Hỗ trợ hàng hóa vật lý, Product Variant, nhiều Warehouse và tồn kho theo từng Variant + Warehouse.
- Việt Nam là Supported Country đầu tiên; quốc gia khác được mở theo từng đợt sau khi hoàn tất yêu cầu thuế, vận chuyển, thanh toán và pháp lý.
- Base Price của Variant được nhập bằng VND. Transaction Currency được quy đổi từ nguồn tỷ giá chuyên dụng và khóa khi tạo Order.
- API độc lập với client, phục vụ Storefront, Admin CMS và các client tương lai.
- Ưu tiên tính đúng tiền, tính nhất quán tồn kho, idempotency, auditability và khả năng khôi phục hơn tối ưu sớm.

### 1.2 Phạm vi repository

Repository chịu trách nhiệm:

- Django REST API và các background worker.
- Database migrations và domain rules.
- OpenAPI 3.1 schema được version hóa.
- Infrastructure definition, Docker và CI/CD cho backend.
- Tài liệu kiến trúc, vận hành và API.

Repository không chứa:

- Storefront frontend.
- Admin CMS frontend.
- Generated TypeScript client của frontend.
- Marketplace hoặc seller portal.

## 2. Actor và phân quyền

### 2.1 Customer

- Đăng ký, xác minh email, đăng nhập và quản lý session.
- Quản lý hồ sơ và nhiều địa chỉ.
- Duyệt/tìm Product, sử dụng Wishlist và Cart.
- Checkout, xem Order, Shipment và Return Request.
- Review Product đã mua và nhận thành công.
- Quản lý consent, yêu cầu anonymize/xóa tài khoản theo chính sách.

### 2.2 Master Admin

- Toàn quyền nghiệp vụ và quản lý staff/role.
- Quản lý provider, security configuration và Supported Country.
- Duyệt action nhạy cảm hoặc Refund vượt ngưỡng.
- Truy cập toàn bộ Audit Log đã được kiểm soát.
- Master Admin là role nghiệp vụ, không đồng nghĩa với Django `is_superuser`.

### 2.3 Store Manager

- Quản lý catalog, Brand, translation, media và publication.
- Quản lý Base Price, Promotion, Gift Card, Warehouse và inventory.
- Quản lý Order và Shipment; duyệt Return/Refund trong hạn mức và quản lý Review.
- Xem analytics và cấu hình không nhạy cảm.
- Không quản lý Master Admin, secret hoặc security configuration nhạy cảm.

### 2.4 Order Staff

- Xem catalog và inventory cần thiết cho xử lý Order.
- Xác nhận, đóng gói, giao hàng và cập nhật Shipment.
- Tiếp nhận/xử lý Return Request theo quyền được giao.
- Chỉ xem analytics giới hạn và Audit Log của thao tác do mình thực hiện.
- Không thay đổi giá, Promotion, Gift Card hoặc staff role.

### 2.5 Ma trận quyền cơ sở

| Chức năng | Master Admin | Store Manager | Order Staff |
|---|:---:|:---:|:---:|
| Staff và role | Quản lý | Không | Không |
| Provider/security | Quản lý | Không | Không |
| Country/currency/tax | Quản lý | Xem | Không |
| Catalog/translation/media | Quản lý | Quản lý | Xem |
| Giá/Promotion/Gift Card | Quản lý | Quản lý | Xem |
| Inventory/Warehouse | Quản lý | Quản lý | Xem |
| Order/Shipment | Quản lý | Quản lý | Xử lý |
| Refund/Return | Quản lý | Duyệt | Xử lý |
| Review moderation | Quản lý | Quản lý | Không |
| Analytics | Toàn bộ | Toàn bộ | Giới hạn |
| Audit Log | Toàn bộ | Chỉ xem | Thao tác của mình |

Role là lớp quyền ban đầu. Mọi action còn phải kiểm tra permission codename và object-level policy trong application service. Không rải `if user.role == ...` trong view.

## 3. Phạm vi chức năng

### 3.1 Accounts

- Email được chuẩn hóa, không phân biệt hoa/thường và duy nhất.
- Entity dùng ID nội bộ bất biến; không dùng email làm foreign key.
- Hỗ trợ email/password và Google login cho Customer.
- Có thể liên kết nhiều phương thức đăng nhập với cùng một Customer.
- Email phải được xác minh trước checkout.
- Quên/đặt lại mật khẩu và đổi email qua quy trình xác minh.
- MFA bắt buộc cho mọi staff.
- Customer xem và thu hồi từng session hoặc tất cả session.
- Vô hiệu hóa Customer thu hồi refresh token nhưng không tự động hủy Order đã xác nhận.
- Yêu cầu xóa tài khoản vô hiệu hóa ngay, sau đó anonymize bất đồng bộ dữ liệu không bắt buộc lưu.

### 3.2 Supported Country, locale và currency

- Một Supported Country định nghĩa currency được phép, locale, tax rules, Shipping Method và Payment Method.
- Lần truy cập đầu có thể gợi ý country/language/currency từ IP và browser locale.
- Customer được đổi lựa chọn thủ công; lựa chọn được lưu vào tài khoản.
- Địa chỉ giao hàng đã xác thực quyết định thuế, vận chuyển và các phương thức khả dụng; IP không phải nguồn quyết định.
- Ra mắt với Việt Nam, tiếng Việt và tiếng Anh.
- Locale mới được thêm mà không thay đổi schema Product chính.

### 3.3 Catalog

- Category dạng cây nhiều cấp, không có vòng lặp cha-con.
- Product có thể thuộc nhiều Category và có một primary Category.
- Hỗ trợ nhiều Brand nhưng tất cả Product vẫn do một Merchant bán.
- Product chứa nội dung trình bày; Variant là đơn vị có thể mua.
- SKU, barcode tùy chọn, Base Price, weight và inventory nằm ở Variant.
- Attribute/Attribute Value linh hoạt và có translation.
- Tổ hợp Attribute của Variant phải duy nhất trong Product.
- SKU duy nhất toàn hệ thống, không tái sử dụng.
- Variant đã xuất hiện trong Order không được đổi SKU hoặc tổ hợp thuộc tính; archive và tạo Variant mới.
- Product lifecycle: `draft`, `active`, `inactive`, `archived`.
- Không hard-delete Product/Variant đã được Order tham chiếu.
- Publish là action riêng; không chỉ `PATCH status`.
- Điều kiện publish: nội dung locale mặc định đầy đủ, ít nhất một Variant bán được và một media đã xử lý.

### 3.4 Translation

- UI/error message dùng Django gettext.
- Product, Category, Brand, Attribute và SEO content dùng translation table theo locale.
- Không tạo cột cố định như `name_vi`, `name_en`.
- AI chỉ tạo bản nháp translation; Store Manager phải duyệt trước publication.
- Locale thiếu translation fallback về locale mặc định và được CMS đánh dấu chưa hoàn tất.
- Alt text của media hỗ trợ theo locale.

### 3.5 Search và recommendation

OpenSearch cung cấp:

- Full-text search đa ngôn ngữ.
- Autocomplete và prefix match.
- Typo tolerance và synonym.
- Faceted filters: Category, price range, Attribute, availability, rating, Promotion và Brand.
- Sorting, popularity, conversion, rating và recency.
- Exact SKU/barcode có độ ưu tiên cao nhất.

Mỗi Product được index thành search document theo locale. PostgreSQL là source of truth; OpenSearch là projection có thể rebuild và chấp nhận eventual consistency. Giá và tồn kho phải được xác minh lại khi thêm Cart và checkout.

Recommendation phiên bản đầu dùng rule-based: cùng Category, thường mua cùng, bán chạy và hành vi cơ bản. Hệ thống ghi event để sau này có thể dùng ML; không dùng ChatGPT tự quyết định recommendation trong request.

### 3.6 Media

- Admin CMS yêu cầu upload credential từ Admin API.
- API tạo `MediaUpload` trạng thái `pending` và trả presigned POST; presigned PUT/multipart dùng khi phù hợp.
- URL sống ngắn, mặc định khoảng 5 phút, và chỉ ghi vào key ngẫu nhiên dưới vùng `quarantine/`.
- Không dùng filename của client làm object key và không cho client đặt ACL public.
- Upload đi thẳng từ frontend tới S3-compatible object storage; Django không proxy file body.
- Worker xác minh size, MIME khai báo, magic bytes và khả năng decode.
- Quét malware, xóa EXIF/GPS, tạo WebP/AVIF và thumbnail.
- File gốc private; chỉ derivative đã duyệt được CDN phân phối.
- Media chuyển sang `ready` hoặc `rejected`; Product chỉ dùng asset `ready`.
- Event object-created có thể lặp nên worker phải idempotent.
- Local dùng MinIO; production dùng managed S3-compatible storage và CDN.

### 3.7 Pricing và exchange rate

- Mỗi Variant có một Base Price bằng VND.
- Customer chọn một Transaction Currency được Supported Country cho phép.
- Exchange Rate lấy từ API tài chính chuyên dụng qua provider adapter; không lấy từ ChatGPT.
- Rate được đồng bộ định kỳ vào PostgreSQL, có nguồn, timestamp và thời hạn.
- Không gọi rate provider trong từng request đọc catalog.
- Không cho checkout khi rate bắt buộc đã quá hạn.
- Order khóa Base Price, Exchange Rate, Transaction Currency, converted amount và rounding.
- Tiền lưu bằng integer minor unit, không dùng `float`.
- VND không có phần thập phân; USD lưu cents; rate dùng decimal có precision cao.

### 3.8 Inventory và Warehouse

Tồn kho được quản lý theo `Variant + Warehouse`:

```text
available_to_sell = on_hand - reserved - safety_stock
```

- `available_to_sell` không được âm.
- Không cho backorder trong phiên bản đầu.
- Checkout tạo Inventory Reservation mặc định 15 phút và có thể cấu hình.
- Thanh toán/xác nhận thành công chuyển reservation thành stock deduction.
- Checkout thất bại, hết hạn hoặc Order bị hủy sẽ giải phóng reservation.
- Mọi nhập, bán, release, return hoặc adjustment tạo Inventory Movement bất biến.
- Manual adjustment bắt buộc có loại, lý do, actor và reference.
- Hàng return chỉ được hoàn tồn sau khi Order Staff kiểm tra.
- Cạnh tranh Variant cuối cùng phải dùng PostgreSQL transaction và row locking để chỉ một checkout thành công.

### 3.9 Cart

- Mỗi Customer chỉ có một Cart active.
- Cart có Transaction Currency hiện tại.
- Đổi currency sẽ tính lại toàn bộ Cart.
- Cart không khóa giá hoặc inventory.
- Mỗi lần đọc Cart/checkout phải tính lại giá, rate, discount và availability.
- Response chỉ rõ những Cart Line đã thay đổi giá hoặc số lượng khả dụng.
- Cart Line không phải Order Line và không được dùng làm chứng từ lịch sử.

### 3.10 Checkout

Luồng chuẩn:

1. Xác minh Customer, Supported Country và Shipping/Billing Address.
2. Kiểm tra Variant còn active và có thể bán.
3. Tính lại Base Price, Exchange Rate, Promotion, tax và shipping quote.
4. Khóa các hàng tồn kho bằng transaction và tạo Inventory Reservation.
5. Giữ tạm Coupon redemption và Gift Card balance nếu có.
6. Tạo Order và Order Line snapshot.
7. Tạo Payment Attempt phù hợp: COD trước, online payment sau.
8. Commit Order, reservation và outbox event trong cùng PostgreSQL transaction.
9. External call, notification và indexing chạy ngoài transaction.

`POST /checkout/orders` bắt buộc `Idempotency-Key`:

- Cùng Customer + key + body trả cùng kết quả.
- Cùng key nhưng body khác trả `409 Conflict`.
- Reservation, Coupon, Gift Card và Payment phải cùng chống lặp.

### 3.11 Công thức Order

```text
Base Price
  x Exchange Rate
  = Converted Unit Price (rounded by currency)

Converted Unit Price
  x Quantity
  = Merchandise Subtotal

Merchandise Subtotal
  - Promotion Discount
  = Discounted Subtotal

Discounted Subtotal
  + Tax
  + Shipping
  = Order Total

Order Total
  - Gift Card Applied
  = Amount Due
```

- Converted unit price được làm tròn trước khi nhân quantity.
- Discount được phân bổ xác định xuống Order Line.
- Rounding remainder được phân bổ xác định, có test invariant.
- Order lưu subtotal, discount, tax, shipping, Gift Card applied, total và amount due riêng biệt.
- Tổng Order luôn bằng tổng các thành phần và Order Line.
- Address, Product name, SKU, price, rate, tax, Promotion và shipping đều được snapshot.

### 3.12 Promotion và Coupon

- Một Customer-entered Coupon tối đa cho mỗi Order.
- Coupon được kết hợp với automatic Promotion khi cả hai `stackable`.
- Hỗ trợ percent discount, fixed amount, free shipping, buy-X-get-Y, Product/Category/Order scope, minimum quantity/value và usage limit.
- Promotion được mô hình bằng `conditions + benefits`; CMS không cho nhập code hoặc biểu thức tùy ý.
- Không giảm tax/shipping trừ khi rule nói rõ.
- Snapshot Promotion và discount allocation được lưu theo Order Line.

### 3.13 Gift Card

- Gift Card là payment instrument, không phải discount.
- Currency cố định; chỉ dùng khi trùng Transaction Currency.
- Tối đa một Gift Card trên mỗi Order trong phiên bản đầu.
- Có thể kết hợp với Coupon.
- Số dư được giữ tạm trong checkout và trừ khi Order xác nhận.
- Gift Card mua online chỉ kích hoạt sau payment thành công.
- Staff có thể phát hành Gift Card theo quyền.
- Mã chỉ hiển thị một lần, lưu dưới dạng hash và không được đổi thành tiền mặt.
- Không dùng Gift Card để mua Gift Card khác.
- Gift Card Ledger bất biến ghi issuance, activation, spending, refund, expiry và adjustment.
- Refund phần đã thanh toán bằng Gift Card được trả lại Gift Card.

### 3.14 Tax

- Tax dựa trên Shipping/Billing Address và luật của Supported Country, không dựa vào IP.
- Việt Nam giai đoạn đầu dùng rule nội bộ được cấu hình và version hóa.
- Giá hiển thị có/không gồm tax tùy quy định của country.
- Order lưu pre-tax amount, tax breakdown và total.
- Khi mở country cần provider bên ngoài, hệ thống không checkout nếu không xác định được tax hợp lệ.
- Chỉ dùng cache nếu provider cho phép và quote chưa hết hạn.
- Không âm thầm fallback tax về 0.

### 3.15 Shipping và Shipment

- Shipping Method có thể dùng rule nội bộ theo country/region, weight và Cart value.
- Hỗ trợ free-shipping threshold.
- External Shipping Provider được thêm qua adapter.
- Quote có hạn và Shipping Method/charge được khóa vào Order.
- Provider lỗi chỉ vô hiệu hóa phương thức cần realtime quote; có thể dùng rule nội bộ hợp lệ.
- Một Order có thể có nhiều Shipment từ nhiều Warehouse hoặc nhiều đợt.
- Shipment có carrier, tracking code, Order Line/quantity và lifecycle riêng.

### 3.16 Payment

- COD là phương thức ưu tiên đầu tiên.
- Online payment được thêm sau qua `PaymentProvider` interface.
- Một Order có thể có nhiều Payment Attempt nhưng amount owed không tăng.
- Payment create/refund luôn dùng provider idempotency key.
- Inbound webhook xác minh signature từ raw body, deduplicate provider event ID và chịu được event sai thứ tự.
- Endpoint webhook ghi nhận nhanh rồi xử lý nghiệp vụ bất đồng bộ.
- Delivery record được redact và có khả năng replay an toàn từ CMS.
- Không xây outbound partner webhook trong phạm vi hiện tại.

### 3.17 Order, Payment và Fulfillment lifecycle

Không dùng một trường `status` duy nhất.

Order lifecycle:

```text
draft -> pending_confirmation -> confirmed -> completed
draft/pending_confirmation -> expired
pending_confirmation/confirmed -> cancelled
```

Payment lifecycle:

```text
pending -> authorized -> captured -> partially_refunded -> refunded
pending/authorized -> failed
authorized -> voided
```

Fulfillment lifecycle:

```text
unfulfilled -> processing -> packed -> shipped -> delivered
processing/packed -> cancelled
shipped -> delivery_failed
```

Return có lifecycle riêng. Mọi transition thực hiện qua action endpoint, không cho CMS `PATCH status` tùy ý.

- Customer tự hủy trước khi Fulfillment chuyển sang `processing`.
- Online payment đã thu tiền phải tạo Refund khi hủy.
- Order/Order Line không bị xóa sau khi tạo.
- Đổi địa chỉ trước fulfillment dùng action riêng và lưu lịch sử.
- Không sửa Product/quantity snapshot âm thầm; dùng adjustment/replacement hoặc hủy và tạo Order mới.
- Mọi chênh lệch tiền tạo Payment/Refund record tương ứng.

### 3.18 Return và Refund

- Return window mặc định 30 ngày từ lúc delivered.
- Category có thể bị loại khỏi chính sách return.
- Customer tạo Return Request theo từng Order Line, quantity, lý do và ảnh.
- Order Staff duyệt, nhận hàng và kiểm tra trước Refund.
- Hỗ trợ partial return và partial refund.
- Exchange được xử lý bằng Return + replacement Order để sổ sách rõ ràng.
- Phí return shipping thuộc Merchant hoặc Customer tùy reason.
- Refund lũy kế không vượt captured amount.
- Refund vượt threshold cấu hình cần Master Admin duyệt.

### 3.19 Wishlist, Review và analytics

Wishlist:

- Một Wishlist mặc định cho mỗi Customer.
- Có thể lưu Product/Variant; hàng hết tồn vẫn hiển thị nhưng không thêm Cart được.

Review:

- Chỉ Customer có Order completed chứa Product mới được review.
- Mỗi Customer một Review cho mỗi Product và được phép sửa.
- Store Manager duyệt, ẩn hoặc phản hồi.
- Aggregate rating chỉ tính Review đã duyệt.

Analytics:

- Operational: revenue, Order count, cancellation/return rate, low stock và best seller.
- Behavioral: view, search, add/remove Cart và checkout abandonment.
- Event dùng anonymous ID hoặc Customer ID phù hợp và tuân thủ consent theo country.
- Không đưa PII không cần thiết vào dashboard.

### 3.20 Notification

- Email transaction là kênh bắt buộc và không phụ thuộc marketing consent.
- Template theo locale.
- Gửi bất đồng bộ và chống gửi trùng.
- Thiết kế adapter để thêm SMS/push sau.

## 4. Trạng thái ngoài phạm vi hiện tại

- Loyalty: chưa làm.
- Marketplace: không làm.
- Online payment: kiến trúc sẵn sàng nhưng triển khai sau COD.
- Subscription/recurring Product: giai đoạn 2.
- ML recommendation: sau khi có đủ dữ liệu hành vi.
- Outbound webhook cho đối tác: chỉ thêm khi có integration thực tế.
- Kubernetes: chưa dùng cho đến khi có nhu cầu vận hành đo được.

## 5. REST API contract

### 5.1 Namespace

```text
/api/v1/storefront/...
/api/v1/admin/...
/api/v1/webhooks/{provider}/...
/api/v1/schema/
/health/live
/health/ready
```

- Storefront chỉ trả dữ liệu đã publish và hợp lệ cho Supported Country.
- Admin trả dữ liệu vận hành theo permission.
- Webhook dùng provider authentication/signature, không dùng staff/Customer JWT.
- Major version nằm trong URL; không version từng module.

### 5.2 Resource convention

- URL dùng danh từ số nhiều.
- CRUD dùng HTTP method.
- Business transition dùng action rõ ràng như `publish`, `cancel`, `approve`, `refund`.
- ID công khai và primary key dùng UUIDv7.
- Mã thân thiện lưu riêng, ví dụ `ORD-2026-000123`.

Ví dụ:

```text
GET    /api/v1/storefront/products
GET    /api/v1/storefront/products/{product_id}
POST   /api/v1/storefront/cart/items
DELETE /api/v1/storefront/cart/items/{item_id}
POST   /api/v1/admin/products/{product_id}/publish
POST   /api/v1/admin/orders/{order_id}/cancel
POST   /api/v1/admin/returns/{return_id}/approve
```

### 5.3 Success response

Resource đơn:

```json
{
  "data": {
    "id": "019...",
    "status": "confirmed",
    "created_at": "2026-08-12T10:30:00Z",
    "updated_at": "2026-08-12T10:30:00Z",
    "version": 1
  },
  "meta": {
    "request_id": "019..."
  }
}
```

Collection:

```json
{
  "data": [],
  "meta": {
    "request_id": "019...",
    "pagination": {
      "next_cursor": "...",
      "has_more": true,
      "page_size": 20
    }
  }
}
```

- Create/update/action trả representation mới nhất đầy đủ theo use case.
- “Đầy đủ” không có nghĩa tải mọi relation hoặc field ngoài quyền người gọi.
- `201 Created` kèm `Location` khi tạo.
- Action đồng bộ trả `200`; action bất đồng bộ trả `202` kèm operation.
- Delete không có representation mới trả `204`.

### 5.4 Error response

Dùng RFC Problem Details mở rộng:

```json
{
  "type": "https://api.example.com/problems/insufficient-stock",
  "title": "Insufficient stock",
  "status": 409,
  "code": "inventory.insufficient_stock",
  "detail": "The requested quantity is no longer available.",
  "instance": "/api/v1/storefront/checkout/orders",
  "errors": [
    {
      "field": "items.0.quantity",
      "code": "available_quantity",
      "message": "Only 2 units are available."
    }
  ],
  "trace_id": "..."
}
```

Frontend phụ thuộc vào `code` ổn định, không phụ thuộc câu chữ message.

### 5.5 JSON representation

- Field, enum và error code dùng tiếng Anh.
- Enum dùng lowercase `snake_case`.
- Datetime dùng ISO 8601 UTC; date dùng `YYYY-MM-DD`.
- ID serialize thành UUIDv7 string.
- Money serialize thành `{ "amount": 4820, "currency": "USD" }`; `amount` luôn là integer minor unit của currency đó. Với currency zero-decimal như VND, minor unit bằng chính major unit nên `amount` là giá trị VND nguyên, không nhân 100.
- Exchange Rate serialize thành decimal string, không JSON float.
- Country/currency/language dùng mã ISO và BCP 47 phù hợp.
- `Accept-Language` chọn translation; `Content-Language` báo locale thực tế/fallback.

### 5.6 Pagination, filter và concurrency

- Cursor pagination cho Product search, Order, Payment, Audit Log và event stream.
- Page-number chỉ cho danh sách cấu hình nhỏ.
- Mặc định 20, tối đa 100; cursor opaque.
- Filter/sort/include theo whitelist; không expose ORM field tùy ý.
- Mutable Admin resource có `version`/ETag; client gửi `If-Match`.
- Version mismatch trả `412 Precondition Failed`.
- Financial/inventory action vẫn dùng database locking và idempotency.

### 5.7 API compatibility

- OpenAPI 3.1 là contract chính thức.
- Commit schema tại `docs/api/openapi.yaml`.
- CI generate, validate và so breaking change với `master`.
- Breaking change cần `/api/v2/` và deprecation window.
- Dùng `Deprecation` và `Sunset` header khi cần.
- Schema được publish dưới dạng CI artifact hoặc `/api/v1/schema/`.
- Frontend repository tự sinh typed client; backend không commit TypeScript client.

## 6. Security và privacy

### 6.1 Authentication

- JWT access token sống khoảng 10–15 phút.
- Refresh token khoảng 30 ngày, rotate và có thể revoke.
- Chỉ lưu hash của refresh session, không lưu raw token.
- Staff session ngắn hơn và bắt buộc MFA.
- Re-auth/MFA gần thời điểm action nhạy cảm.
- Production chỉ chạy HTTPS.
- Password hash dùng Argon2.

### 6.2 Sensitive action

Refund, inventory adjustment, Gift Card issuance, manual Exchange Rate và Customer disable:

- Dùng action endpoint, không dùng CRUD status update.
- Yêu cầu permission và MFA phù hợp.
- Bắt buộc reason.
- Bắt buộc idempotency key khi có side effect; dùng chung header `Idempotency-Key` như checkout ([§3.10](#310-checkout)), không tự đặt tên field riêng theo module.
- Ghi before/after đã redact vào Audit Log.
- Sẵn sàng thêm two-person approval cho giá trị lớn.

### 6.3 Abuse protection

Rate limit riêng theo IP, Customer và endpoint cho:

- Registration/login/MFA/password reset.
- Email verification.
- Search/autocomplete.
- Checkout/Order.
- Coupon/Gift Card validation.
- Media upload.
- Review/Return Request.

Chỉ bật CAPTCHA/challenge khi phát hiện bất thường.

### 6.4 Logging và PII

- Không log password, token, Gift Card code, card data, full payment payload hoặc full address.
- Log ID, state, provider reference và correlation/request ID.
- Redaction tập trung và áp dụng cả API, worker, webhook và Sentry.
- Điều khoản và privacy policy được version hóa.
- Marketing consent tách riêng, mặc định tắt và có thể revoke.

### 6.5 Secrets

- Local dùng `.env`; chỉ commit `.env.example`.
- Production dùng managed secret store.
- Admin API không bao giờ trả secret.
- Secret bắt buộc nằm trong database phải được mã hóa bằng key bên ngoài database.
- Có rotation procedure cho JWT signing key, provider key và database credential.
- GitHub Actions dùng environment secret với least privilege.

## 7. Kiến trúc kỹ thuật

### 7.1 Architectural style

Backend là modular monolith: một Django deployment, một PostgreSQL cluster và các module nghiệp vụ rõ ràng. Đây không phải microservices.

Mục tiêu chính của việc chia module là cấu trúc folder dễ hiểu:

- Code cùng nghiệp vụ nằm cùng chỗ.
- Mỗi module dùng khuôn thư mục nhất quán.
- Module nhỏ không phải tạo folder/file rỗng.
- Khi module lớn, tách model/service/selector theo use case.
- Tránh logic nghiệp vụ trong view, serializer hoặc `common`.

### 7.2 Cấu trúc repository

```text
be-py-eco/
|-- backend/
|   |-- pyproject.toml
|   |-- uv.lock
|   |-- manage.py
|   |-- src/
|   |   |-- config/
|   |   |   |-- settings/
|   |   |   |   |-- base.py
|   |   |   |   |-- local.py
|   |   |   |   |-- test.py
|   |   |   |   `-- production.py
|   |   |   |-- urls.py
|   |   |   |-- celery.py
|   |   |   |-- asgi.py
|   |   |   `-- wsgi.py
|   |   |-- modules/
|   |   |-- integrations/
|   |   `-- common/
|   `-- tests/
|-- infra/
|   |-- docker/
|   `-- compose/
|-- docs/
|   |-- adr/
|   |-- agents/
|   `-- api/
|-- scripts/
|-- .github/workflows/
|-- CLAUDE.md
|-- CONTEXT.md
|-- guild.md
`-- README.md
```

### 7.3 Khuôn Django module

Ví dụ module `catalog` khi đã đủ lớn:

```text
backend/src/modules/catalog/
|-- __init__.py
|-- apps.py
|-- models/
|   |-- product.py
|   |-- variant.py
|   |-- category.py
|   `-- translation.py
|-- api/
|   |-- storefront/
|   |   |-- serializers.py
|   |   |-- views.py
|   |   `-- urls.py
|   `-- admin/
|       |-- serializers.py
|       |-- views.py
|       `-- urls.py
|-- services/
|   |-- create_product.py
|   `-- publish_product.py
|-- selectors/
|   `-- product_catalog.py
|-- events.py
|-- tasks.py
|-- migrations/
`-- tests/
    |-- factories.py
    |-- test_models.py
    |-- test_services.py
    `-- test_api.py
```

Ý nghĩa:

- `models`: dữ liệu và invariant gần entity.
- `api/storefront`: contract chỉ dành cho Customer frontend.
- `api/admin`: contract CMS và permission staff.
- `services`: use case thay đổi state.
- `selectors`: query đọc phức tạp/tối ưu.
- `events`: domain/integration event definitions.
- `tasks`: Celery task của module.
- `tests`: test nằm gần chức năng.

Module nhỏ có thể bắt đầu bằng `models.py`, `services.py`, `selectors.py`; chỉ chuyển thành folder khi có nhiều file/use case.

### 7.4 Danh sách module

| Module | Trách nhiệm |
|---|---|
| `accounts` | Customer/staff, profile, address, auth, MFA, session, consent |
| `localization` | Supported Country, locale, currency và cấu hình khả dụng |
| `catalog` | Category, Brand, Product, Variant, Attribute, Translation |
| `pricing` | Base Price, Exchange Rate, conversion và rounding |
| `search` | OpenSearch projection, indexing và product discovery |
| `inventory` | Warehouse, stock, Reservation và Inventory Movement |
| `carts` | Active Cart và Cart Line |
| `checkout` | Phối hợp validation, quote, reservation và tạo Order |
| `orders` | Order, Order Line, snapshot và lifecycle |
| `payments` | COD, Payment Attempt, webhook, capture và Refund |
| `shipping` | Shipping Method, quote, Shipment và tracking |
| `taxes` | Tax rule/provider, quote và snapshot |
| `promotions` | Promotion, Coupon, condition, benefit và redemption |
| `wishlists` | Wishlist của Customer |
| `reviews` | Verified Review, moderation và aggregate rating |
| `recommendations` | Rule-based recommendation và event input |
| `gift_cards` | Gift Card, balance reservation và Ledger |
| `returns` | Return Request, inspection và replacement workflow |
| `notifications` | Email template, locale và delivery deduplication |
| `analytics` | Operational metrics và behavioral event |
| `media` | Presigned upload, quarantine và derivative processing |
| `outbox` | Transactional event persistence và dispatch |
| `audit` | Immutable staff/customer sensitive-action history |

`checkout` điều phối use case nhưng không trở thành nơi chứa toàn bộ dữ liệu. State lâu dài nằm tại module sở hữu như `orders`, `inventory`, `payments` và `shipping`.

### 7.5 Common

```text
common/
|-- api/              # pagination, error envelope
|-- auth/             # permission primitives
|-- db/               # base model, transaction helpers
|-- money/            # Money, Currency, rounding
|-- ids/              # UUIDv7 and ID helpers
|-- observability/    # logging, tracing, request ID
`-- testing/          # shared test helpers
```

Không đặt Product, Order, Promotion rule hoặc application service vào `common`.

### 7.6 Integrations

Các provider sau có internal interface và adapter riêng:

- Exchange rate.
- Tax.
- Shipping.
- Payment.
- Email/SMS/push.
- Object storage/CDN.
- Analytics export.

Local/test dùng fake provider xác định. Production chọn adapter qua environment/config. Checkout không gọi trực tiếp vendor SDK.

### 7.7 Transactional outbox

- Business state và outbox event commit trong cùng PostgreSQL transaction.
- Dispatcher publish event/task sau commit.
- Consumer idempotent, retry giới hạn và theo dõi failed task.
- Không gọi payment, email, OpenSearch hoặc shipping bên trong database transaction.
- Theo dõi outbox backlog và cảnh báo khi vượt ngưỡng.

## 8. Stack và thư viện

Phiên bản dưới đây là stable baseline đã kiểm tra ngày 2026-08-12. `pyproject.toml` dùng compatible range phù hợp; `uv.lock` khóa phiên bản chính xác và CI kiểm tra vulnerability trước khi cập nhật.

### 8.1 Core API

| Package | Baseline | Công dụng |
|---|---:|---|
| Python | 3.13.x | Runtime cân bằng độ mới và ecosystem compatibility |
| Django | 5.2.17 LTS | ORM, migration, transaction, security và application framework |
| djangorestframework | 3.18.0 | REST API, serializer, permission và throttling |
| psycopg | 3.3.4 | PostgreSQL driver/connection pool |
| django-environ | 0.14.0 | Environment-based configuration |
| django-filter | 26.1 | Whitelisted API filtering |
| drf-spectacular | 0.30.0 | OpenAPI 3.1 generation |
| drf-standardized-errors | 0.16.0 | Standard error responses |
| django-cors-headers | 4.9.0 | CORS cho Storefront/Admin CMS |

### 8.2 Auth và security

| Package | Baseline | Công dụng |
|---|---:|---|
| djangorestframework-simplejwt | 5.5.1 | JWT access/refresh và rotation |
| django-allauth | 65.19.0 | Email verification và Google login |
| django-otp | 1.7.0 | TOTP/MFA cho staff |
| django-axes | 8.3.1 | Brute-force protection |
| argon2-cffi | 25.1.0 | Argon2 password hashing |
| cryptography | 50.0.0 | Cryptographic primitives |
| django-countries | 9.0.0 | Country codes/fields |
| phonenumberslite | 9.0.36 | International phone normalization |

### 8.3 Background và provider

| Package | Baseline | Công dụng |
|---|---:|---|
| celery | 5.6.3 | Background task execution |
| django-celery-beat | 2.9.0 | Periodic schedules |
| redis | 8.1.0 | Redis cache/rate-limit client |
| opensearch-py | 3.2.0 | OpenSearch index/query client |
| httpx | 0.28.1 | External HTTP provider calls |
| tenacity | 9.1.4 | Bounded retry với backoff/jitter |

### 8.4 Media

| Package | Baseline | Công dụng |
|---|---:|---|
| django-storages | 1.14.6 | Django storage backend |
| boto3 | 1.43.69 | S3 API và presigned credential |
| Pillow | 12.3.0 | Decode, resize, metadata removal và derivative |
| filetype | 1.2.0 | Magic-byte file detection |
| ClamAV | Managed system service | Malware scanning qua internal adapter |

### 8.5 Observability

| Package | Baseline | Công dụng |
|---|---:|---|
| structlog | 26.1.0 | Structured JSON logging |
| sentry-sdk | 2.67.1 | Error reporting và tracing |
| prometheus-client | 0.26.0 | Technical/business metrics export |

### 8.6 Testing

| Package | Baseline | Công dụng |
|---|---:|---|
| pytest | 9.1.1 | Test runner |
| pytest-django | 4.14.0 | Django/PostgreSQL test integration |
| pytest-cov | 7.1.0 | Coverage reporting |
| factory-boy | 3.3.3 | Minimal test factories |
| hypothesis | 6.165.3 | Property-based invariant tests |
| freezegun | 1.5.5 | Time boundary tests |
| respx | 0.23.1 | Mock HTTP provider contract |

### 8.7 Development và supply-chain quality

| Package/tool | Baseline | Công dụng |
|---|---:|---|
| uv | Latest pinned toolchain | Dependency, environment và lockfile |
| ruff | 0.16.2 | Lint và format |
| mypy | 2.3.0 | Stable static type checking |
| django-stubs | 6.0.9 | Django ORM type support |
| pip-audit | 2.10.1 | Dependency vulnerability scan |
| bandit | 1.9.4 | Python security static analysis |
| detect-secrets | 1.5.0 | Secret scanning |

Không dùng thư viện generic để thay thế các rule cốt lõi: Money calculation, Inventory Reservation, transactional outbox, idempotency, Promotion engine và Order state machine được project tự sở hữu và kiểm thử.

## 9. Infrastructure và deployment

### 9.1 Thành phần

- PostgreSQL: source of truth và transaction boundary.
- RabbitMQ: Celery broker.
- Redis: cache, throttling/rate-limit và ephemeral coordination; không là source of truth.
- OpenSearch: rebuildable search projection.
- S3-compatible object storage + CDN: media.
- Celery worker: email, indexing, media, provider retry và analytics.
- Scheduler: rate sync, expiry, cleanup và periodic task.
- Outbox dispatcher: publish committed events.

### 9.2 Environment

- Local: Docker Compose với PostgreSQL, RabbitMQ, Redis, OpenSearch, MinIO và fake provider.
- Production: managed container platform; chưa dùng Kubernetes.
- Managed PostgreSQL, RabbitMQ, Redis, OpenSearch và object storage.
- Web, worker, scheduler và outbox dispatcher là process riêng.
- Web/worker autoscale độc lập.
- CI/CD dùng GitHub Actions.

### 9.3 Health

- `/health/live`: chỉ xác nhận process sống, không gọi dependency.
- `/health/ready`: kiểm tra PostgreSQL và dependency bắt buộc.
- Worker có heartbeat/health riêng.
- Dependency không critical như email/OpenSearch lỗi không nhất thiết làm toàn storefront API `not ready`.
- Không expose credential hoặc version nhạy cảm.

### 9.4 Timeout và resilience

- Mọi provider call có connect/read/total timeout.
- Chỉ retry transient error và operation an toàn/idempotent.
- Exponential backoff + jitter, retry có giới hạn.
- Circuit breaker cho provider lỗi kéo dài.
- Task hết retry vào failed queue và tạo alert.
- Không retry vô hạn trong HTTP request.

## 10. Testing strategy

### 10.1 Test pyramid

- Unit test: Money, rounding, transition, Promotion và permission.
- Service test với PostgreSQL thật: checkout, inventory, Order và outbox.
- API test: authentication, authorization, validation và response contract.
- Provider contract test.
- Container integration test: RabbitMQ, Redis, OpenSearch và MinIO.
- Một số ít end-to-end API journey quan trọng.
- Không mock ORM trong domain/service test.

### 10.2 Journey bắt buộc

1. Register → verify email → login.
2. Browse/search Product đa ngôn ngữ và currency.
3. Cart → COD checkout → Order → Shipment → delivered.
4. Hai Customer tranh Variant cuối, chỉ một thành công.
5. Payment webhook lặp không tạo double charge/effect.
6. Reservation hết hạn trả inventory.
7. Coupon + Gift Card + tax + shipping tính tổng đúng.
8. Return một Order Line → partial Refund.
9. Staff thiếu permission bị từ chối.
10. Presigned upload → scan/process → publish.
11. Product update → outbox → OpenSearch projection.
12. Customer deletion anonymize PII nhưng giữ financial records.

### 10.3 Invariant/property tests

- Order total bằng tổng thành phần.
- Discount không vượt phần được giảm.
- Cumulative Refund không vượt captured amount.
- Gift Card balance không âm.
- Inventory availability không âm.
- Cùng idempotency key không tạo thêm effect.
- Currency conversion tuân thủ precision/rounding.

### 10.4 Time tests

Logic thời gian dùng clock abstraction/hàm trung tâm có thể thay trong test:

- Stale Exchange Rate.
- Reservation expiry.
- Coupon/Gift Card expiry boundary.
- Promotion timezone và DST.
- Refresh token rotation.
- Return window 30 ngày.

### 10.5 Database tests

- CI dùng PostgreSQL thật, không dùng SQLite thay thế.
- Test độc lập và factory tối thiểu.
- Test constraint, index và migration.
- Query-count test ngăn N+1.
- Benchmark query quan trọng.

## 11. CI quality gates

Mỗi pull request chạy:

1. `uv lock --check`.
2. Ruff format/lint.
3. Mypy + django-stubs.
4. Migration drift check.
5. Unit/API/integration tests.
6. Coverage cho code mới và đường domain-critical.
7. OpenAPI generate, validate và breaking-change check.
8. `pip-audit`, Bandit và secret scan.
9. Container build.
10. Dependency/license report.

Checkout, payment và inventory cần branch coverage cao cùng mutation testing chọn lọc. Coverage tổng thể không phải tiêu chí duy nhất.

## 12. Observability, audit và vận hành

### 12.1 SLO ban đầu

Mục tiêu percentile 95, không tính thời gian external provider:

- Product detail/Cart read: dưới 300 ms.
- Search: dưới 500 ms.
- Admin list: dưới 700 ms.
- Checkout nội bộ: dưới 1 giây trước provider.
- Availability: 99,9%.

### 12.2 Logs, metrics và tracing

- JSON log với request ID, task ID và business resource ID phù hợp.
- Distributed trace qua API → PostgreSQL → Celery → provider.
- Alert cho payment webhook failure, outbox backlog, reservation anomaly, negative inventory invariant, search lag và failed task.
- Technical metrics và business metrics tách rõ.

### 12.3 Audit Log

- Bất biến và không có update/delete API.
- Ghi actor, action, resource, before/after đã redact, reason, IP, request ID và UTC timestamp.
- Không ghi secret.
- Baseline giữ 2 năm cho administrative action.
- Chỉ Master Admin tra cứu toàn bộ.

### 12.4 Retention baseline

- Financial/tax record: theo nghĩa vụ pháp lý và cấu hình country.
- Audit: 2 năm.
- Redacted webhook payload: 90 ngày.
- Idempotency record: mặc định 7 ngày; payment theo provider policy dài hơn khi cần.
- Abandoned Cart: 90 ngày.
- Raw analytics event: 13 tháng.
- Rejected quarantine media: 7 ngày.
- Expired reservation được cleanup; Inventory Movement vẫn giữ.

### 12.5 Time

- Database lưu UTC.
- API trả timezone-aware ISO 8601.
- Promotion, Gift Card expiry và business report lưu business timezone/rule.
- Không dùng naive datetime.

## 13. Backup, restore và migration

### 13.1 Backup

- PostgreSQL point-in-time recovery.
- Encrypted automated daily backup.
- Baseline retention: daily 30 ngày, monthly 12 tháng; điều chỉnh theo pháp lý.
- Object storage bật versioning/lifecycle.
- OpenSearch có thể rebuild từ PostgreSQL.
- Test restore định kỳ.
- Mục tiêu ban đầu: RPO ≤ 15 phút, RTO ≤ 4 giờ.

### 13.2 Deployment migration

- Migration tương thích với app version trước trong rolling deployment.
- Dùng expand → backfill → switch → contract.
- Không tự động chạy destructive migration.
- Backfill lớn chạy task riêng, có checkpoint.
- CI test migration từ snapshot gần production.
- Rollback app; database ưu tiên forward-fix.

## 14. Seed, feature flag và Definition of Done

### 14.1 Seed data

- Idempotent management command cho local/test.
- Có nhiều locale, currency, Variant và edge case.
- Không dùng production data fixture.
- Production seed chỉ chứa reviewed configuration.
- Không tạo default user/password trong production.

### 14.2 Feature flag

Áp dụng cho online payment, country mới, recommendation, Gift Card và return self-service:

- Scope global/country/customer cohort.
- Mọi thay đổi flag được audit.
- Feature flag không thay thế permission.

### 14.3 Definition of Done

Một API feature chỉ hoàn thành khi:

- Domain rule và permission rõ ràng.
- Migration/index đã review.
- Tests pass.
- OpenAPI và error code cập nhật.
- Idempotency, audit và observability được xử lý khi liên quan.
- Không có secret/vulnerability nghiêm trọng.
- Có migration/rollback strategy.
- Runbook/tài liệu vận hành cập nhật khi cần.
- Schema artifact sẵn sàng cho frontend tích hợp.

## 15. Lộ trình triển khai theo vertical slice

1. Project foundation, authentication và OpenAPI.
2. Catalog, media và translation.
3. Search, pricing và currency conversion.
4. Cart và Inventory Reservation.
5. Checkout, COD và Order.
6. Admin CMS API cho Order và fulfillment.
7. Notification, audit và observability.
8. Promotion và Gift Card.
9. Review, Wishlist và rule-based recommendation.
10. Return/Refund và analytics.
11. Online payment và mở thêm Supported Country.
12. Subscription trong giai đoạn 2.

Mỗi slice phải chạy end-to-end qua API, có migration, OpenAPI và test trước khi chuyển sang slice tiếp theo.

## 16. Quyết định còn phụ thuộc triển khai thực tế

Các điểm sau không được tự suy đoán trong code; phải được chọn trước ticket tương ứng:

- Exchange-rate provider production.
- Tax provider cho từng country ngoài Việt Nam.
- Shipping carrier/provider.
- Online payment provider.
- Email/SMS/push provider.
- Production cloud/container platform.
- S3-compatible provider/CDN.
- Retention và tax policy pháp lý cuối cùng theo Supported Country.
- Domain name dùng trong RFC Problem Details.
- Refund approval threshold.
- Concrete rate limits, SLO alert thresholds và infrastructure sizing.

Provider choice phải được ghi ADR nếu tạo lock-in hoặc có trade-off khó đảo ngược.

## 17. Tài liệu liên quan

- `CONTEXT.md`: glossary và ubiquitous language.
- `docs/adr/0001-opensearch-for-product-discovery.md`.
- `docs/adr/0002-vnd-base-prices-with-locked-conversion.md`.
- `docs/adr/0003-modular-monolith.md`.
- `docs/adr/0004-transactional-outbox.md`.
- `docs/adr/0005-monorepo-for-api-and-frontends.md`: đã superseded.
- `docs/adr/0006-presigned-media-upload-pipeline.md`.
- `docs/adr/0007-backend-only-api-repository.md`.
- `docs/agents/issue-tracker.md`.
- `docs/agents/triage-labels.md`.
- `docs/agents/domain.md`.

## 18. Nguồn kỹ thuật tham khảo

- Django supported releases: <https://www.djangoproject.com/download/>
- Django installation and PostgreSQL guidance: <https://docs.djangoproject.com/en/dev/faq/install/>
- Django REST Framework authentication: <https://www.django-rest-framework.org/api-guide/authentication/>
- DRF schema guidance: <https://www.django-rest-framework.org/api-guide/schemas/>
- drf-spectacular: <https://drf-spectacular.readthedocs.io/en/stable/>
- Celery with Django: <https://docs.celeryq.dev/en/latest/django/first-steps-with-django.html>
- Celery brokers/backends: <https://docs.celeryq.dev/en/latest/getting-started/backends-and-brokers/>
- AWS S3 presigned URLs: <https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html>
- AWS S3 event notifications: <https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html>
