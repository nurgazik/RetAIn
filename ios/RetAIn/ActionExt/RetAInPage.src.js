// Runs inside the Safari page before the extension UI opens (Apple: "Accessing a Webpage").
// Returns the selection (if any), the article text, title and URL to the extension.
// Readability (vendor/, bundled ahead of this file) strips page clutter — share buttons,
// captions, "listen to this article" — and keeps the article's paragraphs; if it finds no
// article, the text falls back to the main element's visible text as before.
var RetAInPage = function () {};
RetAInPage.prototype = {
  article: function () {
    try {
      if (typeof Readability === "undefined") return null;
      var a = new Readability(document.cloneNode(true)).parse();  // clone: parse() mutates the DOM
      if (!a || !a.content) return null;
      // inert document: nothing in it runs or loads while we read its text
      var doc = new DOMParser().parseFromString(a.content, "text/html");
      var blocks = Array.prototype.slice.call(doc.body.querySelectorAll("p, h1, h2, h3, h4, h5, h6, li, blockquote, pre"))
        .filter(function (el) { return !el.querySelector("p, li, blockquote, pre"); })  // innermost blocks only
        .map(function (el) { return {tag: el.tagName, text: (el.textContent || "").replace(/\s+/g, " ").trim()}; })
        .filter(function (b) { return b.text.length > 0; });
      // an opening heading is the headline: it becomes the title, not body text
      var title = a.title || "";
      if (blocks.length && /^H[12]$/.test(blocks[0].tag)) title = blocks.shift().text;
      // RetAIn's own rule on top of Readability: short fragments that aren't sentences
      // ("Listen to this article 7 min") are widgets, not prose; subheadings stay
      blocks = blocks.filter(function (b) {
        return /^H[2-6]$/.test(b.tag) || b.text.split(" ").length >= 8 || /[.!?"”’)]$/.test(b.text);
      });
      var text = blocks.length ? blocks.map(function (b) { return b.text; }).join("\n\n") : (a.textContent || "").trim();
      if (text.split(/\s+/).length < 25) return null;
      return {text: text, title: title, byline: a.byline || "", siteName: a.siteName || "",
              publishedTime: a.publishedTime || ""};
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
      "root": root ? root.tagName : "none"
    });
  },
  finalize: function (arguments) {}
};
var ExtensionPreprocessingJS = new RetAInPage();
