import Foundation

/// Reddit links (D45: read on the phone while the founder is the only user). A link names
/// either a post or one comment (…/comments/<post>/comment/<id>/): the reader takes exactly
/// that — the post's body, or that comment. Reddit first serves a script check page, so the
/// loader waits until the post (and the comment, if named) is on the page.
struct RedditReader: SourceReader {
    let name = "reddit"
    /// Evaluates to {ready, kind, title, author, subreddit, text} on a Reddit thread page.
    static let pageJS = """
        (function () {
          var m = location.pathname.match(/\\/comments\\/[^/]+\\/(?:comment\\/|[^/]+\\/)([a-z0-9]+)/i);
          var post = document.querySelector('shreddit-post');
          var c = m ? document.querySelector('shreddit-comment[thingid="t1_' + m[1] + '"]') : null;
          var body = c ? c.querySelector('[slot=comment]') : (post ? post.querySelector('[slot=text-body]') : null);
          var sub = location.pathname.match(/^\\/(r\\/[^/]+)/);
          return {ready: !!post && (!m || !!c), kind: c ? 'comment' : 'post',
                  title: (post && post.getAttribute('post-title')) || document.title,
                  author: ((c || post) && (c || post).getAttribute('author')) || '',
                  subreddit: sub ? sub[1] : '',
                  text: body ? body.innerText.trim() : ''};
        })()
        """

    func claims(_ input: ShareInput) -> Bool {
        guard let host = input.webURL?.host?.lowercased() else { return false }
        return host == "reddit.com" || host.hasSuffix(".reddit.com") || host == "redd.it"
    }
    func read(_ input: ShareInput) async -> ReaderResult {
        guard let url = input.webURL, let page = await PageLoader.open(url, until: "(\(Self.pageJS)).ready") else {
            return Unusable.pageUnreadable
        }
        return await extract(from: page)
    }
    @MainActor func extract(from page: PageLoader) async -> ReaderResult {
        guard let r = await page.evaluate("JSON.stringify(\(Self.pageJS))") as? String,
              let res = try? JSONSerialization.jsonObject(with: Data(r.utf8)) as? [String: Any],
              res["ready"] as? Bool == true else { return Unusable.pageUnreadable }
        let text = res["text"] as? String ?? "", words = Words.count(text)
        let comment = res["kind"] as? String == "comment"
        guard words >= Words.min else {
            return .unusable(title: comment ? "A short comment" : "A short post",
                             detail: comment ? "That comment is \(words) words; RetAIn needs about \(Words.min). Share a longer one."
                                             : "This post is \(words) words; RetAIn needs about \(Words.min). To read a comment, share that comment instead.")
        }
        var fields: [String: String] = [:]
        if let a = res["author"] as? String, !a.isEmpty { fields["byline"] = "u/" + a }
        if let s = res["subreddit"] as? String, !s.isEmpty { fields["site_name"] = s }
        // the thread's address without the check-page solution and share tracking
        var clean = page.currentURL.flatMap { URLComponents(url: $0, resolvingAgainstBaseURL: false) }
        clean?.query = nil
        return .text(ShareRead(text: text, title: res["title"] as? String, url: clean?.url?.absoluteString,
                               sourceFields: fields, extractor: comment ? "reddit-comment" : "reddit-post"))
    }
}
