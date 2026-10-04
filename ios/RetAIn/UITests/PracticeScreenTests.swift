import XCTest

/// Walks one practice session on the simulator (signed in with the dev token by the unit tests,
/// against the local service) and saves a screenshot per screen to /tmp/retain-practice/.
final class PracticeScreenTests: XCTestCase {
    private let out = URL(fileURLWithPath: "/tmp/retain-practice")

    func testPracticeSessionScreens() throws {
        let app = XCUIApplication()
        app.launch()
        try? FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
        let tab = app.tabBars.buttons["Practice"]
        guard tab.waitForExistence(timeout: 10) else { throw XCTSkip("not signed in on this simulator") }
        tab.tap()

        let fill = app.staticTexts["FILL IN THE WORD"], write = app.staticTexts["USE IT IN A SENTENCE"]
        let done = app.staticTexts["Done for today"]
        XCTAssertTrue(fill.waitForExistence(timeout: 60) || write.exists || done.exists, "practice didn't load")
        var shots = 0
        func shot(_ name: String) {
            shots += 1
            try? app.screenshot().pngRepresentation.write(to: out.appending(path: String(format: "%02d-%@.png", shots, name)))
        }

        var steps = 0
        while steps < 12, !done.exists {
            steps += 1
            if fill.exists {
                shot("fill")
                let field = app.textFields["Type the word"]
                field.tap(); field.typeText("guess")
                app.buttons["Check"].tap()
                XCTAssertTrue(app.buttons["Next"].waitForExistence(timeout: 20))
                shot("fill-result")
                app.buttons["Next"].tap()
            } else if write.exists {
                shot("write")
                let word = app.staticTexts["practice-word"].label
                let field = app.textFields.firstMatch
                field.tap(); field.typeText("Nobody expected the \(word) to matter this much in the end.")
                app.buttons["Check"].tap()
                XCTAssertTrue(app.buttons["Next"].waitForExistence(timeout: 40))
                shot("write-result")
                app.buttons["Next"].tap()
            }
            _ = fill.waitForExistence(timeout: 5) || write.waitForExistence(timeout: 1) || done.waitForExistence(timeout: 1)
        }
        if app.alerts.firstMatch.waitForExistence(timeout: 3) { shot("reminder-offer"); app.alerts.buttons["Not now"].tap() }
        XCTAssertTrue(done.waitForExistence(timeout: 5))
        shot("summary")
    }
}
