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
        func add() {
            let field = app.textFields["Add a word"]
            XCTAssertTrue(field.waitForExistence(timeout: 10))
            field.tap(); field.typeText(word + "\n")
        }
        let row = app.staticTexts[word]
        func scrollToRow() -> Bool {  // new words go last; a long list renders only what's near the screen
            for _ in 0..<25 where !row.exists { app.collectionViews.firstMatch.swipeUp(velocity: .fast) }
            return row.waitForExistence(timeout: 5)
        }

        add()
        sleep(3)  // the card is built server-side
        XCTAssertTrue(scrollToRow(), "word wasn't added")
        row.swipeLeft()
        XCTAssertTrue(app.buttons["Delete"].waitForExistence(timeout: 5))
        shot("swipe-delete")
        app.buttons["Delete"].tap()
        XCTAssertTrue(row.waitForNonExistence(timeout: 10), "deleted word still listed")
        shot("after-delete")

        app.collectionViews.firstMatch.swipeDown(velocity: .fast)
        for _ in 0..<25 where !app.textFields["Add a word"].isHittable { app.collectionViews.firstMatch.swipeDown(velocity: .fast) }
        add()  // saved again: back, fresh
        sleep(3)
        XCTAssertTrue(scrollToRow(), "word didn't come back")
        row.tap()
        XCTAssertTrue(app.buttons["delete-word"].waitForExistence(timeout: 10))
        shot("card-delete")
        app.buttons["delete-word"].tap()
        XCTAssertTrue(app.navigationBars["Words"].waitForExistence(timeout: 10))  // back on the list
        XCTAssertTrue(row.waitForNonExistence(timeout: 10), "deleted word still listed")
    }
}
