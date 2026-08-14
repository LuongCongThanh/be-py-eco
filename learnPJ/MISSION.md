# Mission: Full-stack Engineer (qua Python/Django trong be-py-eco)

## Lý do
Bạn đã biết lập trình bằng một ngôn ngữ khác nhưng chưa từng viết Python.
Mục tiêu dài hạn (từ 2026-08-14) đã mở rộng thành: **trở thành full-stack
engineer** — không chỉ hiểu riêng repo này. `be-py-eco` vẫn là phương
tiện học cụ thể (không học lý thuyết trừu tượng), nhưng mỗi buổi học nên
gắn với tư duy full-stack: truy được luồng dữ liệu qua mọi lớp (request
→ URL → View → ORM → DB → Response), không chỉ nhớ cú pháp một ngôn ngữ.

## Thành công là khi
- Đọc được một file Python trong `src/` (models, views, serializers) và
  giải thích được từng dòng làm gì, không cần tra cứu.
- Viết được một script Python nhỏ từ đầu (functions, classes, control
  flow, các cấu trúc dữ liệu chuẩn) mà không cần nhớ lại cú pháp ngôn ngữ
  cũ.
- Thoải mái với các idiom của Python không có ở hầu hết ngôn ngữ khác
  (list/dict comprehension, context manager, duck typing, decorator) — đủ
  để nhận ra và dùng được các trường hợp đơn giản.
- Giải thích được sự khác biệt giữa một khái niệm Python và khái niệm
  tương đương trong ngôn ngữ bạn đã biết, khi được hỏi.
- Truy được một request thật trong `be-py-eco` đi qua từng lớp (URL →
  View → Service → ORM → DB → Response) và tự giải thích lại bằng lời
  của mình, không cần đọc lại trang lesson.

## Ràng buộc
- Đã biết các khái niệm lập trình tổng quát (biến, hàm, vòng lặp, điều
  kiện, OOP) từ ngôn ngữ khác — bài học nên dựa vào nền tảng đó thay vì
  dạy lại từ số 0.
- Học theo từng buổi rải rác theo thời gian, trong workspace `learnPJ/`
  nằm ngay trong repo `be-py-eco`.
- Mục tiêu cuối là Django/DRF trong repo này, nhưng đó là **giai đoạn 2**
  — chưa nhảy vào nội dung riêng của framework trước khi nền tảng Python
  vững.

## Cập nhật mission (giai đoạn 2 bắt đầu)
Sau bài 7 (Python cốt lõi), bạn chọn bỏ qua bài tập thực hành tổng hợp
(bài 8) và chuyển thẳng sang Django/DRF. Từ đây, Django/DRF **nằm trong
phạm vi**, không còn "ngoài phạm vi" nữa — xem
[[learning-records/0002-skipped-practice-jumped-to-django]].

## Cập nhật mission (2026-08-14 — mở rộng thành full-stack engineer)
Sau bài 16 (permissions), bạn xác nhận đã đọc bài 9-16 nhưng không nắm
được Django cơ bản — xem
[[learning-records/0003-coverage-without-retention-even-at-basics]].
Cùng lúc, bạn đặt câu hỏi lớn hơn: muốn học *mindset* để trở thành
full-stack engineer, không chỉ học riêng Django cho repo này. Hai điều
này liên quan: cách sửa vấn đề retention (đọc trang HTML không tạo ra
hiểu) chính là tư duy full-stack thực chiến — truy luồng dữ liệu thật,
tự giải thích lại bằng lời, viết được test — không phải đọc tuyến tính
thêm bài mới. Từ đây, "full-stack engineer" là mục tiêu dài hạn; Django
trong `be-py-eco` là bài tập cụ thể đầu tiên để rèn tư duy đó.

## Ngoài phạm vi (hiện tại)
- Async/await, metaprogramming nâng cao, C extension — chủ đề nâng cao,
  để sau nhiều.
- Deployment, Docker, hạ tầng — đã có riêng ở
  [docs/agents/how-to-run.md](../docs/agents/how-to-run.md), không thuộc
  mission học Python này.
