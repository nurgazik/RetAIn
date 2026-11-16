import XCTest

/// "Use it in a sentence": with the keyboard up, the field and Check stay in view (2026-11-16).
/// Screenshots go to $SHOTS_DIR/retain-write-keyboard.
final class WriteKeyboardScreenTests: XCTestCase {
    func testTheFieldStaysAboveTheKeyboard() throws {
        let app = XCUIApplication()
        app.launch()
        let tab = app.tabBars.buttons["Practice"]
        guard tab.waitForExistence(timeout: 10) else { throw XCTSkip("not signed in on this simulator") }
        tab.tap()
        if app.alerts.firstMatch.waitForExistence(timeout: 3) { app.alerts.buttons["Not now"].tap() }
        let card = app.buttons.containing(.staticText, identifier: "Use it in a sentence").firstMatch
        XCTAssertTrue(card.waitForExistence(timeout: 60), "chooser didn't load")
        guard card.isEnabled else { throw XCTSkip("no sentence left today") }
        card.tap()
        let field = app.textFields.firstMatch
        XCTAssertTrue(field.waitForExistence(timeout: 30))
        let dir = URL(fileURLWithPath: ProcessInfo.processInfo.environment["SHOTS_DIR"] ?? NSTemporaryDirectory())
            .appending(path: "retain-write-keyboard")
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        field.tap()
        XCTAssertTrue(app.keyboards.firstMatch.waitForExistence(timeout: 5))
        sleep(1)  // the keyboard and any scroll finish animating
        try? app.screenshot().pngRepresentation.write(to: dir.appending(path: "1-keyboard-up.png"))
        field.typeText("Despite the adversity she faced in her first year abroad, she kept going and")
        sleep(1)
        try? app.screenshot().pngRepresentation.write(to: dir.appending(path: "2-typing.png"))
        let kb = app.keyboards.firstMatch.frame
        XCTAssertLessThanOrEqual(field.frame.maxY, kb.minY, "the field is under the keyboard")
        XCTAssertLessThanOrEqual(app.buttons["Check"].frame.maxY, kb.minY, "Check is under the keyboard")
    }
}
