// Runs inside the Safari page before the extension UI opens (Apple: "Accessing a Webpage").
// Returns the selection (if any), the article text, title and URL to the extension.
var RetAInPage = function () {};
RetAInPage.prototype = {
  run: function (arguments) {
    var selection = "";
    try { selection = String(window.getSelection() || ""); } catch (e) {}
    var root = document.querySelector("article") ||
               document.querySelector("main") ||
               document.querySelector('[role="main"]') ||
               document.body;
    var text = root ? (root.innerText || "") : "";
    arguments.completionFunction({
      "title": document.title || "",
      "url": document.baseURI || "",
      "selection": selection,
      "text": text,
      "root": root ? root.tagName : "none"
    });
  },
  finalize: function (arguments) {}
};
var ExtensionPreprocessingJS = new RetAInPage();
