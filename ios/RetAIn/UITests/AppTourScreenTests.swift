import XCTest

/// A look at every tab and the reader (D70: the notebook look on each screen). Read-only: nothing is
/// changed. Screenshots in /tmp/retain-tour/ — run it once in light and once in dark appearance.
final class AppTourScreenTests: XCTestCase {
    private let out = URL(fileURLWithPath: "/tmp/retain-tour")

    func testEveryTab() throws {
        let app = XCUIApplication()
        app.launch()
        try? FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
        guard app.tabBars.buttons["Practice"].waitForExistence(timeout: 10) else { throw XCTSkip("not signed in on this simulator") }
        func shot(_ name: String) { try? app.screenshot().pngRepresentation.write(to: out.appending(path: "\(name).png")) }
        if app.alerts.firstMatch.waitForExistence(timeout: 2) { app.alerts.buttons["Not now"].tap() }

        app.tabBars.buttons["Words"].tap()
        XCTAssertTrue(app.navigationBars["Words"].waitForExistence(timeout: 10))
        sleep(2); shot("1-words")
        let firstWord = app.cells.element(boundBy: 2)  // 0: the Add row, 1: the section header
        if firstWord.waitForExistence(timeout: 5) { firstWord.tap(); sleep(2); shot("2-word-card") }

        app.tabBars.buttons["My Reads"].tap()
        XCTAssertTrue(app.navigationBars["My Reads"].waitForExistence(timeout: 10))
        sleep(2); shot("3-reads")
        let firstRead = app.cells.firstMatch
        if firstRead.waitForExistence(timeout: 5) {
            firstRead.tap(); sleep(4); shot("4-reader")
            if app.buttons["Done"].exists { app.buttons["Done"].tap() }
        }

        app.tabBars.buttons["Settings"].tap()
        XCTAssertTrue(app.navigationBars["Settings"].waitForExistence(timeout: 10))
        sleep(1); shot("5-settings")
    }
}
