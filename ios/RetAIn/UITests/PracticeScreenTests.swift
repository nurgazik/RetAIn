import XCTest

/// Walks one practice session on the simulator (signed in with the dev token by the unit tests,
/// against the local service) and saves a screenshot per screen to /tmp/retain-practice/.
/// Starts with sentences, leaves part-way, then does the fill-ins (D57: any order, either one), then
/// the checkpoint between rounds and one card of the next round (D60).
final class PracticeScreenTests: XCTestCase {
    private let out = URL(fileURLWithPath: "/tmp/retain-practice")

    func testPracticeSessionScreens() throws {
        let app = XCUIApplication()
        app.launch()
        try? FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
        let tab = app.tabBars.buttons["Practice"]
        guard tab.waitForExistence(timeout: 10) else { throw XCTSkip("not signed in on this simulator") }
        tab.tap()

        let fillCard = app.buttons.containing(.staticText, identifier: "Fill in the word").firstMatch
        let writeCard = app.buttons.containing(.staticText, identifier: "Use it in a sentence").firstMatch
        XCTAssertTrue(writeCard.waitForExistence(timeout: 60), "chooser didn't load")
        var shots = 0
        func shot(_ name: String) {
            shots += 1
            try? app.screenshot().pngRepresentation.write(to: out.appending(path: String(format: "%02d-%@.png", shots, name)))
        }
        shot("chooser")
        if app.alerts.firstMatch.exists { app.alerts.buttons["Not now"].tap() }

        if writeCard.isEnabled {
            writeCard.tap()
            XCTAssertTrue(app.staticTexts["USE IT IN A SENTENCE"].waitForExistence(timeout: 10))
            shot("write")
            let word = app.staticTexts["practice-word"].label
            let field = app.textFields.firstMatch
            field.tap(); field.typeText("Nobody expected the \(word) to matter this much in the end.")
            app.buttons["Check"].tap()
            XCTAssertTrue(app.buttons["Next"].waitForExistence(timeout: 40))
            shot("write-result")
            app.buttons["Next"].tap()
            if app.alerts.firstMatch.waitForExistence(timeout: 2) { app.alerts.buttons["Not now"].tap() }
            if app.buttons["Exercises"].exists { app.buttons["Exercises"].tap() }  // leave part-way
            XCTAssertTrue(writeCard.waitForExistence(timeout: 5))
            shot("chooser-after-one-sentence")
        }

        if fillCard.isEnabled {
            fillCard.tap()
            let fill = app.staticTexts["FILL IN THE WORD"]
            var steps = 0
            while steps < 15, fill.waitForExistence(timeout: 5) {
                steps += 1
                shot("fill")
                let pill = app.buttons["hint-option"].firstMatch
                if steps == 1 {  // the first fill-in uses the Hint (D58): a pill counts like typing
                    if !pill.exists { app.buttons["Hint"].tap() }
                    XCTAssertTrue(pill.waitForExistence(timeout: 20), "hint pills didn't appear")
                    shot("hint")
                    var i = 0
                    while !app.buttons["Next"].exists, i < 4 {  // wrong pills stay on the card: try the next
                        let options = app.buttons.matching(identifier: "hint-option")
                        let open = (0..<options.count).map { options.element(boundBy: $0) }.first { $0.isEnabled }
                        open?.tap(); i += 1
                        if i == 1, !app.buttons["Next"].waitForExistence(timeout: 10) { shot("wrong-pill") }
                    }
                } else {  // a wrong guess keeps the card (D58); then a pill to finish the word
                    let field = app.textFields["fill-input"]  // D65: typing goes into the gap (focused on arrival)
                    field.typeText("gu")
                    if steps == 2 { shot("typing") }
                    field.typeText("ess")
                    app.buttons["Check"].tap()
                    XCTAssertTrue(app.staticTexts["Not quite: try again. Tap the red word to see what it means."].waitForExistence(timeout: 20))
                    if steps == 2 { shot("wrong-try") }
                    if !pill.exists { app.buttons["Hint"].tap() }
                    XCTAssertTrue(pill.waitForExistence(timeout: 20))
                    var i = 0
                    while !app.buttons["Next"].exists, i < 4 {
                        let options = app.buttons.matching(identifier: "hint-option")
                        let open = (0..<options.count).map { options.element(boundBy: $0) }.first { $0.isEnabled }
                        open?.tap(); i += 1
                        _ = app.buttons["Next"].waitForExistence(timeout: 10)
                    }
                }
                XCTAssertTrue(app.buttons["Next"].waitForExistence(timeout: 20))
                shot("fill-result")
                if steps == 1 {  // D65: the solved word opens its card
                    app.descendants(matching: .any)["solved-word"].tap()
                    XCTAssertTrue(app.buttons["Got it — mark retained"].waitForExistence(timeout: 15), "word card didn't open")
                    shot("word-card")
                    app.swipeDown(velocity: .fast)
                    XCTAssertTrue(app.buttons["Next"].waitForExistence(timeout: 5))
                }
                app.buttons["Next"].tap()
                if app.alerts.firstMatch.waitForExistence(timeout: 2) { shot("reminder-offer"); app.alerts.buttons["Not now"].tap() }
            }
        }
        if app.buttons["next-round"].waitForExistence(timeout: 5) {  // D60: a checkpoint between rounds
            shot("checkpoint")
            app.buttons["next-round"].tap()
            XCTAssertTrue(app.staticTexts["FILL IN THE WORD"].waitForExistence(timeout: 30), "next round didn't start")
            shot("next-round")
            app.buttons["Exercises"].tap()
        }
        XCTAssertTrue(writeCard.waitForExistence(timeout: 5), "back on the chooser")
        shot("chooser-end")
    }
}
