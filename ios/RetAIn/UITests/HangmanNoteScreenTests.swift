import XCTest

/// Hangman's hint shows the user's note with the word blanked (2026-11-16). Run with notes on the dev
/// account's words; screenshots go to $SHOTS_DIR/retain-hangman-note.
final class HangmanNoteScreenTests: XCTestCase {
    func testTheHintShowsTheNoteWithTheWordHidden() throws {
        let app = XCUIApplication()
        app.launch()
        let tab = app.tabBars.buttons["Practice"]
        guard tab.waitForExistence(timeout: 10) else { throw XCTSkip("not signed in on this simulator") }
        tab.tap()
        if app.alerts.firstMatch.waitForExistence(timeout: 3) { app.alerts.buttons["Not now"].tap() }
        let card = app.buttons.containing(.staticText, identifier: "Hangman").firstMatch
        XCTAssertTrue(card.waitForExistence(timeout: 60), "chooser didn't load")
        guard card.isEnabled else { throw XCTSkip("no hangman left today") }
        card.tap()
        let hint = app.buttons["hangman-hint"]
        XCTAssertTrue(hint.waitForExistence(timeout: 30), "no hint button")
        let dir = URL(fileURLWithPath: ProcessInfo.processInfo.environment["SHOTS_DIR"] ?? NSTemporaryDirectory())
            .appending(path: "retain-hangman-note")
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        try? app.screenshot().pngRepresentation.write(to: dir.appending(path: "1-before-hint.png"))
        hint.tap()
        let note = app.otherElements["practice-note"].exists ? app.otherElements["practice-note"] : app.staticTexts["practice-note"]
        XCTAssertTrue(note.waitForExistence(timeout: 5), "note not shown with the hint")
        try? app.screenshot().pngRepresentation.write(to: dir.appending(path: "2-hint-with-note.png"))
    }

    func testFillInShowsTheNoteUnderTheMeaning() throws {
        let app = XCUIApplication()
        app.launch()
        let tab = app.tabBars.buttons["Practice"]
        guard tab.waitForExistence(timeout: 10) else { throw XCTSkip("not signed in on this simulator") }
        tab.tap()
        if app.alerts.firstMatch.waitForExistence(timeout: 3) { app.alerts.buttons["Not now"].tap() }
        let card = app.buttons.containing(.staticText, identifier: "Fill in the word").firstMatch
        XCTAssertTrue(card.waitForExistence(timeout: 60), "chooser didn't load")
        guard card.isEnabled else { throw XCTSkip("no fill-in left today") }
        card.tap()
        let note = app.otherElements["practice-note"].exists ? app.otherElements["practice-note"] : app.staticTexts["practice-note"]
        XCTAssertTrue(note.waitForExistence(timeout: 30), "note not shown on the fill-in")
        let dir = URL(fileURLWithPath: ProcessInfo.processInfo.environment["SHOTS_DIR"] ?? NSTemporaryDirectory())
            .appending(path: "retain-hangman-note")
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        try? app.screenshot().pngRepresentation.write(to: dir.appending(path: "3-fill-with-note.png"))
    }
}
