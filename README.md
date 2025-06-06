# GreenBuy
Migrate db bang alembic
alembic revision --autogenerate -m "Replace is_buyer with role enum"
confirm
alembic upgrade head
