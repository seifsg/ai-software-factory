//! Which URLs the roast may abuse without asking: only apps served on this machine.

/// True for an http(s) URL whose host is local: `localhost`, `*.localhost`, `*.test`, `127.0.0.0/8` or `::1`.
/// Why: the worst-user round submits junk and clicks everything; a shared or live site must never get that unasked.
pub fn is_local(url: &str) -> bool {
    let Some(rest) = url.strip_prefix("http://").or_else(|| url.strip_prefix("https://")) else { return false };
    let authority = rest.split(['/', '?', '#']).next().unwrap_or_default();
    let hostport = authority.rsplit('@').next().unwrap_or_default();
    let host = match hostport.strip_prefix('[') {
        Some(v6) => v6.split(']').next().unwrap_or_default(),
        None => hostport.split(':').next().unwrap_or_default(),
    }
    .to_ascii_lowercase();
    let host = host.strip_suffix('.').unwrap_or(&host);
    host == "localhost"
        || host.ends_with(".localhost")
        || host.ends_with(".test")
        || host == "::1"
        || loopback_v4(host)
}

fn loopback_v4(host: &str) -> bool {
    host.parse::<std::net::Ipv4Addr>().is_ok_and(|ip| ip.is_loopback())
}

#[cfg(test)]
mod tests {
    use super::is_local;

    #[test]
    fn local_hosts_only() {
        for u in ["http://localhost:5173/", "https://app.localhost", "http://shop.test/a?b", "http://127.0.0.1:8080", "http://127.9.9.9", "http://[::1]:3000/x", "http://LOCALHOST.", "http://u:p@localhost:1"] {
            assert!(is_local(u), "{u}");
        }
        for u in ["https://example.com", "http://localhost.evil.com", "http://10.0.0.1", "http://0.0.0.0:80", "ftp://localhost", "localhost:3000", "http://evil.com@", "http://test", "http://[::2]", ""] {
            assert!(!is_local(u), "{u}");
        }
    }
}
