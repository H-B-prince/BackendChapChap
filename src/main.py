from database import engine, SessionLocal, Base


def main():
    db = SessionLocal()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    main()
