// Runs inside the Safari page before the extension UI opens (Apple: "Accessing a Webpage").
// Returns the selection (if any), the article text, title and URL to the extension.
// Readability (vendor/, bundled ahead of this file) strips page clutter — share buttons,
// captions, "listen to this article" — and keeps the article's paragraphs; if it finds no
// article, the text falls back to the main element's visible text as before.
// Page metadata (summary, sub-headline, byline, site, date) is returned as separate fields
// for the reader's header; it never becomes body text, so the model never sees it.
var RetAInPage = function () {};
RetAInPage.prototype = {
  // A copy of the page without short text the reader can't see (collapsed tooltips such as
  // CBC's "audio version is AI-generated" note). Readability only checks inline style and
  // hidden/aria-hidden, not CSS. Long hidden text stays: a collapsed "read more" is article.
  visibleClone: function () {
    var MARK = "data-retain-hidden", marked = [];
    try {
      var els = document.body.querySelectorAll("*");
      for (var i = 0; i < els.length; i++) {
        var el = els[i];
        if (el.parentElement && el.parentElement.hasAttribute(MARK)) continue;
        var hidden = el.checkVisibility ? !el.checkVisibility()
          : (function (s) { return s.display === "none" || s.visibility === "hidden"; })(getComputedStyle(el));
        if (hidden && (el.textContent || "").split(/\s+/).length < 80) { el.setAttribute(MARK, ""); marked.push(el); }
      }
      var clone = document.cloneNode(true);
      var gone = clone.querySelectorAll("[" + MARK + "]");
      for (var j = 0; j < gone.length; j++) gone[j].remove();
      return clone;
    } catch (e) {
      return document.cloneNode(true);
    } finally {
      for (var k = 0; k < marked.length; k++) marked[k].removeAttribute(MARK);  // leave the page as we found it
    }
  },
  article: function () {
    try {
      if (typeof Readability === "undefined") return null;
      var a = new Readability(this.visibleClone()).parse();  // a clone: parse() mutates the DOM
      if (!a || !a.content) return null;
      // inert document: nothing in it runs or loads while we read its text
      var doc = new DOMParser().parseFromString(a.content, "text/html");
      var blocks = Array.prototype.slice.call(doc.body.querySelectorAll("p, h1, h2, h3, h4, h5, h6, li, blockquote, pre"))
        .filter(function (el) { return !el.querySelector("p, li, blockquote, pre"); })  // innermost blocks only
        .map(function (el) {
          var t = el.querySelector("time");
          return {tag: el.tagName, text: (el.textContent || "").replace(/\s+/g, " ").trim(),
                  datetime: t ? (t.getAttribute("datetime") || t.textContent || "") : null};
        })
        .filter(function (b) { return b.text.length > 0; });
      // an opening heading is the headline: it becomes the title, not body text
      var title = a.title || "";
      if (blocks.length && /^H[12]$/.test(blocks[0].tag)) title = blocks.shift().text;
      // RetAIn's own rule on top of Readability: short fragments that aren't sentences
      // ("Listen to this article 7 min") are widgets, not prose; subheadings stay. First, so
      // a section label ("British Columbia") or byline fragment can't hide the header below
      blocks = blocks.filter(function (b) {
        return /^H[2-6]$/.test(b.tag) || b.text.split(" ").length >= 8 || /[.!?"”’)]$/.test(b.text);
      });
      // header lines before the first body paragraph: the summary (it matches the page's
      // meta description), a sub-headline, and a dateline. Summary and sub-headline move to
      // the header as the dek; the dateline goes (its date is kept as publishedTime). A
      // summary counts only when a sub-headline or dateline confirms we're in the header —
      // on some sites the description is simply the lede, which must stay in the body.
      var norm = function (s) { return (s || "").replace(/\s+/g, " ").replace(/(…|\.\.\.)$/, "").trim(); };
      var desc = document.querySelector('meta[name="description"], meta[property="og:description"], meta[name="twitter:description"]');
      var excerpt = norm(desc && desc.getAttribute("content")), published = a.publishedTime || "";
      var lead = [], header = false;
      for (var n = 0; blocks.length && n < 6; n++) {
        var b = blocks[0], words = b.text.split(" ").length;
        if (words < 25 && (b.datetime !== null ||
            (/^[\s·•|–—-]*(posted|published|updated|last updated)\b/i.test(b.text) && /\d/.test(b.text)))) {
          if (!published && b.datetime) published = b.datetime;
          header = true; blocks.shift(); continue;
        }
        var subhead = /^H[2-4]$/.test(b.tag) && words <= 30;
        if (subhead || (excerpt.length >= 40 && norm(b.text).indexOf(excerpt) === 0)) {
          header = header || subhead; lead.push(blocks.shift()); continue;
        }
        break;
      }
      if (!header) { blocks = lead.concat(blocks); lead = []; }  // no header here: put them back
      var dek = lead.map(function (b) { return b.text; });       // page order: summary, sub-headline
      var text = blocks.length ? blocks.map(function (b) { return b.text; }).join("\n\n") : (a.textContent || "").trim();
      if (text.split(/\s+/).length < 25) return null;
      return {text: text, title: title, byline: a.byline || "", siteName: a.siteName || "",
              publishedTime: published, dek: dek.join("\n\n")};
    } catch (e) { return null; }
  },
  run: function (arguments) {
    var selection = "";
    try { selection = String(window.getSelection() || ""); } catch (e) {}
    var a = this.article();
    var root = document.querySelector("article") ||
               document.querySelector("main") ||
               document.querySelector('[role="main"]') ||
               document.body;
    arguments.completionFunction({
      "title": (a && a.title) || document.title || "",
      "url": document.baseURI || "",
      "selection": selection,
      "text": a ? a.text : (root ? (root.innerText || "") : ""),
      "extractor": a ? "readability" : "innerText",
      "byline": a ? a.byline : "",
      "siteName": a ? a.siteName : "",
      "publishedTime": a ? a.publishedTime : "",
      "dek": a ? a.dek : "",
      "root": root ? root.tagName : "none"
    });
  },
  finalize: function (arguments) {}
};
var ExtensionPreprocessingJS = new RetAInPage();
