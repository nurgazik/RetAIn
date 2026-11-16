import XCTest

/// The system edge swipe goes back (2026-11-16): out of an exercise to the chooser, and from a word's card to
/// the Words list. Practice exercises became real pushed screens for this; word cards always were.
final class SwipeBackScreenTests: XCTestCase {
    private func swipeFromLeftEdge(_ app: XCUIApplication) {
        let start = app.coordinate(withNormalizedOffset: CGVector(dx: 0.005, dy: 0.5))
        start.press(forDuration: 0.05, thenDragTo: app.coordinate(withNormalizedOffset: CGVector(dx: 0.85, dy: 0.5)))
    }

    func testSwipeBackFromAnExercise() throws {
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
        XCTAssertTrue(app.staticTexts["HANGMAN"].waitForExistence(timeout: 30), "exercise didn't open")
        swipeFromLeftEdge(app)
        XCTAssertTrue(card.waitForExistence(timeout: 5) && card.isHittable, "edge swipe didn't go back to the chooser")
        XCTAssertFalse(app.staticTexts["HANGMAN"].exists)
        card.tap()   // and back in again: the exercise opens fresh
        XCTAssertTrue(app.staticTexts["HANGMAN"].waitForExistence(timeout: 30), "exercise didn't open again")
        app.navigationBars.buttons.firstMatch.tap()   // the system back button
        XCTAssertTrue(card.waitForExistence(timeout: 5) && card.isHittable, "back button didn't go back")
    }

    func testSwipeBackFromAWordCard() throws {
        let app = XCUIApplication()
        app.launch()
        let tab = app.tabBars.buttons["Words"]
        guard tab.waitForExistence(timeout: 10) else { throw XCTSkip("not signed in on this simulator") }
        tab.tap()
        let row = app.collectionViews.buttons.element(boundBy: 1)  // 0 is "Add"; 1 the first word
        XCTAssertTrue(row.waitForExistence(timeout: 20), "Words list didn't load")
        row.tap()
        let onCard = app.buttons["note-add"].waitForExistence(timeout: 10) || app.staticTexts["note-text"].exists
        XCTAssertTrue(onCard, "card didn't open")
        swipeFromLeftEdge(app)
        XCTAssertTrue(row.waitForExistence(timeout: 5) && row.isHittable, "edge swipe didn't go back to the list")
        XCTAssertFalse(app.buttons["note-add"].exists || app.staticTexts["note-text"].exists, "still on the card")
    }

    /// Fill-in's keyboard still comes up by itself now that the exercise is a pushed screen.
    func testFillInOpensTheKeyboardOnArrival() throws {
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
        XCTAssertTrue(app.keyboards.firstMatch.waitForExistence(timeout: 3), "the keyboard didn't come up")
    }
}
