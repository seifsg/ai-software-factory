//! Which URLs the roast may open: a plain http(s) URL, and without `FACTORY_ROAST_ANY_HOST=1` only on this machine.

/// The URL's lowercase host; `None` unless it is a plain http(s) URL with a host.
/// Refuses whitespace, control characters, quotes, backticks and `\` anywhere: browsers read `\` as `/`, so
/// `http://evil.com\@localhost` would pass a naive host split and open evil.com.
pub fn host(url: &str) -> Option<String> {
    if url.chars().any(|c| c.is_whitespace() || c.is_control() || matches!(c, '\\' | '\'' | '"' | '`')) {
        return None;
    }
    let (scheme, rest) = url.split_once("://")?;
    if scheme != "http" && scheme != "https" {
        return None;
    }
    let authority = rest.split(['/', '?', '#']).next()?;
    let hostport = authority.rsplit('@').next()?;
    let host = match hostport.strip_prefix('[') {
        Some(v6) => v6.split(']').next()?,
        None => hostport.split(':').next()?,
    }
    .to_ascii_lowercase();
    (!host.is_empty()).then_some(host)
}

/// True for a URL whose host is local: `localhost`, `*.localhost`, `*.test`, `127.0.0.0/8` or `::1`.
/// Why: the worst-user round submits junk and clicks everything; a shared or live site must never get that unasked.
pub fn is_local(url: &str) -> bool {
    host(url).is_some_and(|host| {
        let host = host.strip_suffix('.').unwrap_or(&host);
        host == "localhost"
            || host.ends_with(".localhost")
            || host.ends_with(".test")
            || host == "::1"
            || host.parse::<std::net::Ipv4Addr>().is_ok_and(|ip| ip.is_loopback())
    })
}

#[cfg(test)]
mod tests {
    use super::{host, is_local};

    #[test]
    fn local_hosts_only() {
        for u in ["http://localhost:5173/", "https://app.localhost", "http://shop.test/a?b", "http://127.0.0.1:8080", "http://127.9.9.9", "http://[::1]:3000/x", "http://LOCALHOST.", "http://u:p@localhost:1"] {
            assert!(is_local(u), "{u}");
        }
        for u in [
            "https://example.com",
            "http://localhost.evil.com",
            "http://10.0.0.1",
            "http://0.0.0.0:80",
            "ftp://localhost",
            "localhost:3000",
            "http://evil.com@",
            "http://test",
            "http://[::2]",
            "http://evil.com\\@localhost/",
            "http://localhost /x",
            "http://localhost/\u{7}",
            "http://localhost/'x",
            "",
        ] {
            assert!(!is_local(u), "{u}");
        }
    }

    #[test]
    fn host_of_a_plain_url_only() {
        assert_eq!(host("http://127.0.0.1:47811/a?b#c").as_deref(), Some("127.0.0.1"));
        assert_eq!(host("https://Shop.TEST").as_deref(), Some("shop.test"));
        assert_eq!(host("https://"), None);
    }
}
