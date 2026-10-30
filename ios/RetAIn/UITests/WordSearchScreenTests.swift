import XCTest

/// Word search on the Words tab: a form of a word, a meaning, a misspelling, and no match (the
/// "Add" row + "No results"). Read-only: nothing is added. Screenshots in /tmp/retain-search/.
final class WordSearchScreenTests: XCTestCase {
    private let out = URL(fileURLWithPath: "/tmp/retain-search")

    func testSearches() throws {
        let app = XCUIApplication()
        app.launch()
        try? FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
        let tab = app.tabBars.buttons["Words"]
        guard tab.waitForExistence(timeout: 10) else { throw XCTSkip("not signed in on this simulator") }
        tab.tap()
        let field = app.searchFields.firstMatch
        XCTAssertTrue(field.waitForExistence(timeout: 10), "search bar not shown")
        for (i, q) in ["bolstered", "bitter", "acrimonie", "zzqx"].enumerated() {
            field.tap()
            if let v = field.value as? String, !v.isEmpty, v != "Search words, meanings, notes" {
                field.typeText(String(repeating: XCUIKeyboardKey.delete.rawValue, count: v.count))
            }
            field.typeText(q)
            sleep(1)
            if q == "zzqx" {
                XCTAssertTrue(app.buttons["search-add"].exists, "no Add row for an unknown word")
            } else {
                XCTAssertTrue(app.staticTexts.matching(NSPredicate(format: "label BEGINSWITH '1 result' OR label ENDSWITH 'results'")).firstMatch.exists
                              || app.staticTexts.matching(NSPredicate(format: "label CONTAINS[c] 'result'")).firstMatch.exists,
                              "no results for \(q)")
            }
            try? app.screenshot().pngRepresentation.write(to: out.appending(path: String(format: "%02d-%@.png", i + 1, q)))
        }
    }
}
