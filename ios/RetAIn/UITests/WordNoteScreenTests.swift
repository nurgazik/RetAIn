import XCTest

/// D59: adds a note to the first learning word on the simulator (signed in with the dev token by
/// the unit tests, against the local service), saves a screenshot per step to /tmp/retain-notes/,
/// then clears the note again so the account is left as it was. Skips a word that already has one.
final class WordNoteScreenTests: XCTestCase {
    private let out = URL(fileURLWithPath: "/tmp/retain-notes")

    func testAddEditAndClearANote() throws {
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
        let row = app.collectionViews.buttons.element(boundBy: 1)  // 0 is "Add"; 1 the first word
        XCTAssertTrue(row.waitForExistence(timeout: 20), "word list didn't load")
        row.tap()

        let add = app.buttons["note-add"]
        guard add.waitForExistence(timeout: 10) else { throw XCTSkip("the first word already has a note") }
        shot("card-without-note")
        add.tap()
        let field = app.textFields["note-field"]
        XCTAssertTrue(field.waitForExistence(timeout: 5))
        field.typeText("перевод: укреплять. Like my coach before the final.")
        shot("editing")
        app.buttons["note-save"].tap()
        XCTAssertTrue(app.staticTexts["note-text"].waitForExistence(timeout: 10), "note didn't save")
        shot("card-with-note")

        app.navigationBars.buttons.firstMatch.tap()  // back to the list: the row shows the note icon
        XCTAssertTrue(app.images["Has a note"].waitForExistence(timeout: 10))
        shot("list-with-note-icon")

        row.tap()  // clear it again
        XCTAssertTrue(app.buttons["Edit"].waitForExistence(timeout: 10))
        app.buttons["Edit"].tap()
        let edit = app.textFields["note-field"]
        XCTAssertTrue(edit.waitForExistence(timeout: 5))
        edit.press(forDuration: 1.2)
        if app.menuItems["Select All"].waitForExistence(timeout: 2) { app.menuItems["Select All"].tap() }
        edit.typeText(XCUIKeyboardKey.delete.rawValue)
        app.buttons["note-save"].tap()
        XCTAssertTrue(app.buttons["note-add"].waitForExistence(timeout: 10), "note didn't clear")
    }
}
