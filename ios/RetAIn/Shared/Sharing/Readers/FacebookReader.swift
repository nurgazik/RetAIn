import Foundation

/// Facebook links (D46: read on the phone while the founder is the only user). Facebook can't
/// share a single comment, so a link means its post. Logged out, Facebook shows public posts;
/// a private group's post lands on the group's front page and a friends-only post on the login
/// page — each gets its own message. Facebook's markup is machine-generated, so the post is
/// found by content instead: the one block whose text starts with the page's own preview
/// (og:description), inside the post's container when present (data-successful-render-id =
/// the post id). A long post is cut at "See more": the reader taps it and waits for the text to
/// grow (a trailing "…" proves nothing: some posts end on one as a cliffhanger).
struct FacebookReader: SourceReader {
    let name = "facebook"
    /// Evaluates to {state: "post" | "private-group" | "login" | "none", …} on any Facebook page.
    static let pageJS = """
        (function () {
          var meta = function (p) { var m = document.querySelector('meta[property="' + p + '"]'); return m ? m.content || '' : ''; };
          var name = meta('og:title').replace(/\\s*\\|\\s*Facebook\\s*$/, '');
          if (/^\\/share\\//.test(location.pathname)) return {state: 'none'};   // still redirecting: a preview page
          if (/^\\/login/.test(location.pathname)) return {state: 'login'};
          // a group's front page, not a post in it: where a private group's post lands (checked
          // before posts: the group's About text starts with its preview text too)
          if (/^\\/groups\\/[^/]+\\/?$/.test(location.pathname)) return {state: 'private-group', name: name};
          var id = new URLSearchParams(location.search).get('story_fbid');
          var box = id ? document.querySelector('[data-successful-render-id="' + id + '"]') : null;
          var prefix = meta('og:description').replace(/(\\.\\.\\.|…)\\s*$/, '').trim().slice(0, 60);
          var post = null;
          if (prefix) {
            Array.prototype.forEach.call((box || document).querySelectorAll('div[dir=auto], span[dir=auto]'), function (e) {
              var t = (e.innerText || '').trim();
              if (t.indexOf(prefix) === 0 && (!post || t.length > post.length)) post = t;
            });
          }
          if (post) return {state: 'post', name: name, text: post.replace(/\\s*See more\\s*$/, '').trim(),
                            ellipsis: /(…|\\.\\.\\.)\\s*(See more)?\\s*$/.test(post)};
          return {state: 'none'};
        })()
        """
    /// Settled: a post, a login page, or a group page once its name has loaded.
    static let ready = "(function (s) { return s.state === 'post' || s.state === 'login' || (s.state === 'private-group' && !!s.name); })(\(pageJS))"
    /// Finds the post's text block again (same rule as `pageJS`), for the See more lookup.
    /// What expands the post (seen 2026-09-27): tapping its text's own collapsed container
    /// (role=button, aria-expanded=false). Fallback: the first "... See more" button after the
    /// post's text (the container holds the page's other posts too, each with its own).
    /// Tapped when `click`, else just looked for.
    static func seeMoreJS(click: Bool) -> String { """
        (function () {
          var og = document.querySelector('meta[property="og:description"]');
          var prefix = ((og && og.content) || '').replace(/(\\.\\.\\.|…)\\s*$/, '').trim().slice(0, 60);
          if (!prefix) return false;
          var post = Array.prototype.find.call(document.querySelectorAll('div[dir=auto], span[dir=auto]'),
                                               function (e) { return (e.innerText || '').trim().indexOf(prefix) === 0; });
          if (!post) return false;
          // the tap target is the post text's own collapsed container; else a "See more" button after it
          var b = post.closest('[role=button][aria-expanded="false"]') ||
                  Array.prototype.find.call(document.querySelectorAll('[role=button]'), function (e) {
            return /^\\s*(\\.\\.\\.|…)?\\s*See more\\s*$/.test(e.innerText || '') &&
                   (post.compareDocumentPosition(e) & Node.DOCUMENT_POSITION_FOLLOWING);
          });
          if (b && \(click)) b.click();
          return !!b;
        })()
        """ }

    func claims(_ input: ShareInput) -> Bool {
        guard let host = input.webURL?.host?.lowercased() else { return false }
        return host == "facebook.com" || host.hasSuffix(".facebook.com") || host == "fb.watch" || host == "fb.me"
    }
    func read(_ input: ShareInput) async -> ReaderResult {
        guard let url = input.webURL,
              let page = await PageLoader.open(url, until: Self.ready) else { return Self.notShown }
        return await extract(from: page)
    }
    @MainActor func extract(from page: PageLoader) async -> ReaderResult {
        guard var res = await state(page) else { return Self.notShown }
        var cut = false
        // A post cut at "…": its "See more" is drawn before Facebook's code answers taps, so tap,
        // give it a second to grow, and tap again — up to 6 tries.
        if res["state"] as? String == "post", res["ellipsis"] as? Bool == true,
           await page.wait(until: Self.seeMoreJS(click: false), timeout: .seconds(3)) {
            let grown = "((\(Self.pageJS)).text || '').length > \((res["text"] as? String ?? "").count)"
            cut = true
            for _ in 0..<6 where cut {
                _ = await page.evaluate(Self.seeMoreJS(click: true))
                cut = !(await page.wait(until: grown, timeout: .seconds(1)))
            }
            res = await state(page) ?? res
        }
        let name = res["name"] as? String ?? ""
        switch res["state"] as? String {
        case "post":
            let text = res["text"] as? String ?? "", words = Words.count(text)
            guard words >= Words.min else {
                return .unusable(title: "A short post", detail: "This post is \(words) words; RetAIn needs about \(Words.min) to work with.")
            }
            var fields = ["site_name": "Facebook"]
            if !name.isEmpty { fields["byline"] = name }
            return .text(ShareRead(text: text, title: name.isEmpty ? nil : "\(name) on Facebook", url: page.currentURL?.absoluteString,
                                   sourceFields: fields, extractor: cut ? "facebook-post-cut" : "facebook-post"))
        case "private-group":
            return .unusable(title: "This post is in a private group",
                             detail: "\(name.isEmpty ? "The group" : "“\(name)”") only shows its posts to members, so RetAIn can't open it. Copy the post's text and share that instead.")
        case "login":
            return .unusable(title: "Facebook wants a login for this post",
                             detail: "It's probably shared with friends only, so RetAIn can't open it. Copy the post's text and share that instead.")
        default:
            return Self.notShown
        }
    }
    @MainActor private func state(_ page: PageLoader) async -> [String: Any]? {
        guard let json = await page.evaluate("JSON.stringify(\(Self.pageJS))") as? String else { return nil }
        return try? JSONSerialization.jsonObject(with: Data(json.utf8)) as? [String: Any]
    }
    static let notShown = ReaderResult.unusable(title: "Facebook didn't show us this post",
                                                detail: "Copy the post's text and share that instead.")
}
