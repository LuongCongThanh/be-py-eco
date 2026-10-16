# Các bước viết một API (Django REST Framework)

## Vì sao có file này

Đây là **bản đồ tổng quan**, không phải một lesson tuần tự trong `lessons/`.
Bạn đang ở Phase 1 (Python Fundamentals) của `roadmap.md`, còn cách khá xa
Phase Django/DRF nơi bạn sẽ thực sự viết các bước dưới đây. Mục đích của
file này là giúp bạn hình dung trước bức tranh lớn — *khi tới lúc*, mỗi
mục sẽ trở thành một lesson thật với bài tập thực hành riêng.

Phạm vi: từ lúc thiết kế một resource đến khi có test cơ bản chạy được.
**Không bao gồm** deployment/CI-CD — theo `MISSION.md`, phần đó để giai
đoạn sau khi core Python/Django/DRF đã vững.

Version pin theo repo: Python 3.13, Django 5.2.17, DRF 3.18.0 (xem
[[RESOURCES.md]]).

## Lưu ý: be-py-eco không viết DRF "sách giáo khoa"

Tutorial DRF chính thức thường dạy `ModelViewSet` + `Router`, gọi thẳng
ORM trong view. **be-py-eco làm khác** — mỗi bước dưới đây sẽ ghi rõ cách
chuẩn DRF trước, rồi ghi chú "be-py-eco làm khác thế nào" ngay sau, để bạn
không bỡ ngỡ khi sau này đọc code thật và thấy nó không giống lý thuyết.

Điểm khác biệt lớn nhất, biết trước cho đỡ ngợp:

- **`APIView` thay vì `ModelViewSet`** — mỗi endpoint là một class tường
  minh, không có router tự sinh URL.
- **Service layer** — view không đụng ORM trực tiếp, mà gọi một hàm trong
  `services/` chứa business logic. View chỉ lo request/response.
- **API tách theo actor**: `api/admin/` và `api/storefront/` là hai bộ
  serializer/view/url riêng biệt cho cùng một module, không dùng chung.
- **Response bọc trong "envelope"** — mọi response đi qua
  `common.api.envelope.success_envelope`, không trả JSON thô.
- **`drf-spectacular`** sinh OpenAPI schema từ decorator `@extend_schema`
  trên view, không viết doc tay.

---

## 1. Thiết kế resource & endpoint

Trước khi viết code: resource này là gì (danh từ, ví dụ "Customer",
"SupportedCountry"), verb/HTTP method nào cần (GET/POST/PATCH/DELETE),
URL path là gì, request/response shape ra sao. Làm bước này trên giấy
trước, đừng nhảy thẳng vào code.

- Chuẩn DRF: nghĩ theo REST resource — URL là danh từ số nhiều
  (`/customers/`), method quyết định hành động.
- be-py-eco: còn phải quyết **actor** trước — admin hay storefront gọi
  endpoint này? Hai actor có thể cần shape response khác nhau cho cùng
  một resource.
- Ví dụ thật trong repo:
  [`src/modules/localization/api/storefront/urls.py`](../../src/modules/localization/api/storefront/urls.py)
  — endpoint `GET /suggestion` dành riêng cho storefront.

## 2. Model

Định nghĩa dữ liệu cần lưu bằng Django ORM (`models.Model`), field, ràng
buộc (`unique`, `null`), và `Meta.db_table`.

- Chuẩn DRF/Django: kế thừa `django.db.models.Model`.
- be-py-eco: kế thừa `common.db.models.BaseModel` (base class dùng chung
  toàn repo) thay vì `models.Model` trực tiếp.
- Ví dụ thật:
  [`src/modules/localization/models.py`](../../src/modules/localization/models.py)
  — model `SupportedCountry`.

## 3. Migration

Sinh file migration từ thay đổi model (`makemigrations`), rồi áp dụng
vào database (`migrate`). Đây là bước Django tự động hoá — bạn không tự
viết SQL.

- Chuẩn Django: `python manage.py makemigrations <app> && python manage.py migrate`.
- be-py-eco: không khác biệt lớn, nhưng mỗi module có migration riêng
  trong `src/modules/<module>/migrations/` (modular monolith — xem
  [[docs/adr/0003-modular-monolith.md]] ở repo root nếu tò mò).

## 4. Serializer

Định nghĩa cách chuyển dữ liệu Python/model ↔ JSON, và validate input.

- Chuẩn DRF: `ModelSerializer` tự sinh field từ model, dùng chung cho cả
  đọc lẫn ghi.
- be-py-eco: nhiều serializer chỉ khai báo field thủ công
  (`serializers.Serializer`), tách riêng serializer cho *response* và
  serializer cho *request* nếu shape khác nhau — không phải lúc nào cũng
  `ModelSerializer`.
- Ví dụ thật:
  [`src/modules/localization/api/storefront/serializers.py`](../../src/modules/localization/api/storefront/serializers.py)
  — `LocaleSuggestionResponseSerializer` chỉ để mô tả response, không
  validate.

## 5. View

Xử lý request: nhận input, gọi logic xử lý, trả response.

- Chuẩn DRF: `ModelViewSet` gộp list/create/retrieve/update/delete vào
  một class, đăng ký qua `Router`.
- be-py-eco: `APIView` với method tường minh (`def get(self, request)`),
  và **view không tự xử lý logic** — nó gọi một function trong
  `services/`, rồi bọc kết quả bằng `success_envelope` trước khi trả về.
- Ví dụ thật:
  [`src/modules/localization/api/storefront/views.py`](../../src/modules/localization/api/storefront/views.py)
  — `LocaleSuggestionView.get()` gọi
  `modules.localization.services.suggest_locale.suggest_locale(...)`.

## 6. Service layer (logic thật nằm ở đây)

Hàm thuần chứa business logic, không biết gì về HTTP/request/response —
nhận input đơn giản, trả kết quả đơn giản, dễ test độc lập với view.

- Đây **không phải** khái niệm DRF chuẩn — là quy ước riêng của
  be-py-eco để tách business logic khỏi HTTP layer.
- Ví dụ thật:
  [`src/modules/localization/services/suggest_locale.py`](../../src/modules/localization/services/suggest_locale.py)

## 7. URL routing

Gắn view vào một path cụ thể trong `urls.py` của module, rồi include vào
URL config gốc của project.

- Chuẩn Django: `path("resource/", ViewClass.as_view(), name="...")`.
- be-py-eco: mỗi module có `urls.py` riêng cho từng actor
  (`api/admin/urls.py`, `api/storefront/urls.py`) — không gộp chung.
- Ví dụ thật:
  [`src/modules/localization/api/storefront/urls.py`](../../src/modules/localization/api/storefront/urls.py)

## 8. Authentication & Permission cơ bản

Quyết định ai được gọi endpoint này: cần đăng nhập không, cần quyền gì.

- Chuẩn DRF: khai báo `authentication_classes` / `permission_classes`
  trên view, dùng permission có sẵn (`IsAuthenticated`, `AllowAny`, ...).
- be-py-eco: có thêm permission tuỳ biến theo actor trong
  `src/modules/accounts/api/permissions.py` — không chỉ dùng permission
  có sẵn của DRF.
- Ví dụ thật: `LocaleSuggestionView` ở bước 5 khai báo
  `permission_classes = [AllowAny]` vì endpoint này public.

## 9. API docs (OpenAPI)

Mô tả endpoint (summary, request/response shape) để sinh schema/docs tự
động, không viết tay markdown riêng cho API docs.

- be-py-eco dùng `drf-spectacular`: decorator `@extend_schema(...)` đặt
  trên method của view, khai báo `request=`, `responses=`.
- Ví dụ thật: decorator `@extend_schema` trong
  [`src/modules/localization/api/storefront/views.py`](../../src/modules/localization/api/storefront/views.py)

## 10. Test cơ bản

Viết test cho service (logic thuần) và test cho API (gọi qua HTTP client,
kiểm tra status code + response shape).

- be-py-eco dùng `pytest` + `pytest-django` (xem
  [[lessons/0013-pytest-django-basics]] khi tới lesson đó — hiện đã bị
  xoá khỏi workspace theo lịch sử ghi trong `MISSION.md`, sẽ được viết lại
  khi tới đúng phase).
- Ví dụ thật:
  [`src/modules/localization/tests/test_suggest_locale.py`](../../src/modules/localization/tests/test_suggest_locale.py)
  (test service) và
  [`src/modules/accounts/tests/test_api.py`](../../src/modules/accounts/tests/test_api.py)
  (test API qua HTTP).

---

## Tóm tắt luồng

```text
Thiết kế resource/endpoint (actor: admin hay storefront?)
        ↓
Model (BaseModel) → Migration
        ↓
Serializer (request/response, không luôn là ModelSerializer)
        ↓
Service function (business logic thuần, test độc lập được)
        ↓
View (APIView, gọi service, bọc response bằng success_envelope)
        ↓
URL routing (theo actor: api/admin/urls.py hoặc api/storefront/urls.py)
        ↓
Auth/Permission (permission_classes, có thể tuỳ biến theo actor)
        ↓
API docs (@extend_schema cho drf-spectacular)
        ↓
Test (service test + API test)
```

Deployment/CI-CD: ngoài phạm vi file này — xem `MISSION.md` mục "Out of
scope".
