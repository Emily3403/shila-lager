from shila_lager.utils import startup


def pytest_configure() -> None:
    startup()

# @fixture(scope="session")
# def db() -> Generator[DatabaseSession, None, None]:
#     init_database()
#
#     with DatabaseSessionMaker() as session:
#         yield session
