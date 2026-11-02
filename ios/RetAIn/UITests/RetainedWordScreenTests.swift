import XCTest

/// D71: the Words menu (Show · Sort by) and bringing a retained word back with "Learn again". Marks one word
/// retained and back, so its schedule starts over (dev account only). Screenshots in /tmp/retain-retained/.
final class RetainedWordScreenTests: XCTestCase {
    private let out = URL(fileURLWithPath: "/tmp/retain-retained")

    func testFilterSortAndLearnAgain() throws {
        let app = XCUIApplication()
        app.launch()
        try? FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
        guard app.tabBars.buttons["Words"].waitForExistence(timeout: 10) else { throw XCTSkip("not signed in on this simulator") }
        func shot(_ name: String) { try? app.screenshot().pngRepresentation.write(to: out.appending(path: "\(name).png")) }
        if app.alerts.firstMatch.waitForExistence(timeout: 2) { app.alerts.buttons["Not now"].tap() }
        app.tabBars.buttons["Words"].tap()
        let menu = app.buttons["words-filter"]
        XCTAssertTrue(menu.waitForExistence(timeout: 10))
        func choose(_ option: String) { menu.tap(); let b = app.buttons[option]; XCTAssertTrue(b.waitForExistence(timeout: 5)); b.tap(); sleep(1) }  // let the menu close before the next tap

        // a learning word → retained, from its card
        choose("Learning")
        let first = app.cells.element(boundBy: 2)  // 0: the Add row, 1: the section header
        XCTAssertTrue(first.waitForExistence(timeout: 10))
        let word = first.staticTexts.firstMatch.label
        first.tap()
        XCTAssertTrue(app.buttons["Got it — mark retained"].waitForExistence(timeout: 10))
        app.buttons["Got it — mark retained"].tap()

        choose("Retained")
        menu.tap(); sleep(1); shot("1-menu"); app.tap()
        let retained = app.staticTexts[word]
        XCTAssertTrue(retained.waitForExistence(timeout: 10), "\(word) not among retained words")
        shot("2-retained")
        retained.tap()
        XCTAssertTrue(app.buttons["learn-again"].waitForExistence(timeout: 10))
        shot("3-card-learn-again")
        app.buttons["learn-again"].tap()
        XCTAssertFalse(app.staticTexts[word].waitForExistence(timeout: 3), "still listed as retained")

        choose("All"); choose("Newest first")
        sleep(1); shot("4-all-newest")
        choose("A–Z")
        XCTAssertFalse(app.buttons["words-filter"].label.isEmpty)
    }
}
