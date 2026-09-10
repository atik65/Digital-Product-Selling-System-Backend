import uvicorn


def main():
    print("Hello from digital-product-selling-system!")


if __name__ == "__main__":
    main()
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
