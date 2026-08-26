---
name: test-author
description: Author unittest golden, negative, and unit tests for relations.
---

Viết test `unittest.TestCase` trong `tests/{unit,golden,negative,regression}/`. Tên nêu hành vi. Golden đọc fixture đã commit. Negative tamper một field. Không pytest, không mock `relations/`, không gọi SP1 prove. Mỗi test một lý do fail.
