import XCTest

/// D62: add a word, delete it with a swipe, and it's gone from the list; add it again and delete it
/// from its card. Leaves the dev account as it was (the word ends deleted, i.e. hidden).
/// Screenshots in /tmp/retain-delete/.
final class DeleteWordScreenTests: XCTestCase {
    private let out = URL(fileURLWithPath: "/tmp/retain-delete")
    private let word = "perspicacious"

    func testDeleteFromTheListAndFromTheCard() throws {
        let app = XCUIApplication()
        app.launch()
        try? FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
        var shots = 0
        func shot(_ name: String) {
            shots += 1
            try? app.screenshot().pngRepresentation.write(to: out.appending(path: String(format: "%02d-%@.png", shots, name)))
        }
        let tab = app.tabBars.buttons["Words"]
        guard tab.waitForExistence(timeout: 10) else { throw XCTSkip("not signed in on this simulator") }
        tab.tap()
        // Found through search, so it sits at the top: a long A–Z list puts it anywhere, and a row left under
        // the floating search bar or the tab bar can't be swiped.
        let search = app.searchFields.firstMatch
        XCTAssertTrue(search.waitForExistence(timeout: 10))
        search.tap(); search.typeText(word)
        let addRow = app.buttons["search-add"], row = app.staticTexts[word]
        if !addRow.waitForExistence(timeout: 5), row.exists {  // left saved by an earlier failed run: clear it first
            row.swipeLeft(); app.buttons["Delete"].tap()
        }
        XCTAssertTrue(addRow.waitForExistence(timeout: 10), "no Add row for \(word)")
        addRow.tap()  // saved from search (D63)
        XCTAssertTrue(row.waitForExistence(timeout: 20), "word wasn't added")
        row.swipeLeft()
        XCTAssertTrue(app.buttons["Delete"].waitForExistence(timeout: 5))
        shot("swipe-delete")
        app.buttons["Delete"].tap()
        XCTAssertTrue(row.waitForNonExistence(timeout: 10), "deleted word still listed")
        shot("after-delete")

        XCTAssertTrue(addRow.waitForExistence(timeout: 10), "a deleted word can be saved again")
        addRow.tap()  // saved again: back, fresh
        XCTAssertTrue(row.waitForExistence(timeout: 20), "word didn't come back")
        row.tap()
        XCTAssertTrue(app.buttons["delete-word"].waitForExistence(timeout: 10))
        shot("card-delete")
        app.buttons["delete-word"].tap()
        XCTAssertTrue(app.navigationBars["Words"].waitForExistence(timeout: 10))  // back on the list
        XCTAssertTrue(row.waitForNonExistence(timeout: 10), "deleted word still listed")
    }
}
