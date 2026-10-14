FROM rust:alpine AS builder

WORKDIR /app

RUN apk add --no-cache musl-dev

COPY Cargo.toml Cargo.lock ./

RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release

COPY src ./src

RUN touch src/main.rs
RUN cargo build --release

FROM alpine:latest

WORKDIR /app

COPY --from=builder /app/target/release/rustBotCheck /app/rustBotCheck

CMD ["./rustBotCheck"]