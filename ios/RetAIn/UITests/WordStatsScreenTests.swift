import XCTest

/// D74: opens the first word on the simulator (signed in with the dev token by the unit tests, against the
/// local service) and scrolls to the stats list at the end of its card. Screenshots go to $SHOTS_DIR
/// (set TEST_RUNNER_SHOTS_DIR) or the temporary folder.
final class WordStatsScreenTests: XCTestCase {
    func testStatsListAtTheEndOfTheCard() throws {
        let app = XCUIApplication()
        app.launch()
        let out = URL(fileURLWithPath: ProcessInfo.processInfo.environment["SHOTS_DIR"] ?? NSTemporaryDirectory())
            .appending(path: "retain-word-stats")
        try? FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
        func shot(_ name: String) { try? app.screenshot().pngRepresentation.write(to: out.appending(path: "\(name).png")) }

        let tab = app.tabBars.buttons["Words"]
        guard tab.waitForExistence(timeout: 10) else { throw XCTSkip("not signed in on this simulator") }
        tab.tap()
        let row = app.collectionViews.buttons.element(boundBy: 1)  // 0 is "Add"; 1 the first word
        XCTAssertTrue(row.waitForExistence(timeout: 20), "word list didn't load")
        row.tap()
        let stats = app.descendants(matching: .any)["word-stats"]
        for _ in 0..<8 where !(stats.exists && stats.isHittable) { app.swipeUp() }
        XCTAssertTrue(stats.waitForExistence(timeout: 10), "no stats list on the card")
        XCTAssertTrue(app.staticTexts["Shown in reading"].waitForExistence(timeout: 10), "stats didn't load")
        shot("1-stats")
        app.swipeUp()
        shot("2-stats-more")
    }
}
