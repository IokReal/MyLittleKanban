use std::{
    io::{prelude::*, BufReader},
    net::{TcpListener, TcpStream},
};
use chrono::Utc;
use sha256::digest;

fn main() {
    let listener = TcpListener::bind(("0.0.0.0", 9255)).unwrap();
    for stream in listener.incoming() {
        let stream = stream.unwrap();
        handle_connection(stream);
    }
}

fn handle_connection(mut stream: TcpStream) {
    let response200 = "HTTP/1.1 200 OK\r\n\r\n";
    let response403 = "HTTP/1.1 403 Forbidden\r\n\r\n";
    let secret_salt = "BigfishForCat";

    let mut token = String::new();
    let mut ip = String::new();

    {
        let buf_read = BufReader::new(&mut stream);
        for line in buf_read.lines() {
            let line = line.unwrap();
            if line.is_empty() {
                break;
            }
            if line.starts_with("Cookie:") {
                let cookies = line.trim_start_matches("Cookie:").trim();
                for cookie in cookies.split(';') {
                    let cookie = cookie.trim();
                    if cookie.starts_with("pow_token=") {
                        token = cookie.strip_prefix("pow_token=").unwrap_or("").to_string();
                        continue;
                    }
                }
            }
            if line.starts_with("X-Real-IP:") {
                ip = line.trim_start_matches("X-Real-IP:").trim().to_string();
                continue;
            }
            if !(token.is_empty() || ip.is_empty()) {
                break;
            }
        }
    }
    
    print!("pow_token={}; ip:{}", token, ip);

    if token.is_empty() || ip.is_empty() {
        stream.write_all(response403.as_bytes()).unwrap();
        return;
    }

    //===================================================================================================
    let current_utc = Utc::now().timestamp();

    let data: Vec<&str> = token.split(':').collect(); // ${timestamp}:${nonce}:${hash} 

    if data.len() != 3 {
        print!(" f1");
        stream.write_all(response403.as_bytes()).unwrap();
        return;
    }

    if !data[2].starts_with("0000") {
        print!(" f2");
        stream.write_all(response403.as_bytes()).unwrap();
        return;
    }

    let timestamp = data[0].parse::<i64>().unwrap_or(0);

    if (current_utc - timestamp) > 600 || (timestamp - current_utc) > 60 {
        print!(" f3");
        stream.write_all(response403.as_bytes()).unwrap();
        return;
    }

    // `${ip}:${timestamp}:${nonce}:${salt}`
    let raw_string = format!("{}{}{}{}", ip, data[0], data[1], secret_salt);
    let hash = digest(raw_string);

    if hash != data[2] {
        print!(" f4");
        stream.write_all(response403.as_bytes()).unwrap();
        return;
    }

    print!(" ok");
    stream.write_all(response200.as_bytes()).unwrap();
}