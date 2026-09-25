import XCTest

/// Drives Safari in the simulator: page already opened via `simctl openurl`, tap Share,
/// pick the RetAInize action, wait for the transformed sheet. Findings go to SharedStore's
/// spike.log (written by the extension) and a screenshot at OUT_DIR.
final class SafariExtensionTests: XCTestCase {
    let outDir = ProcessInfo.processInfo.environment["OUT_DIR"] ?? NSTemporaryDirectory()
    let actionName = ProcessInfo.processInfo.environment["ACTION_NAME"] ?? "RetAInize"

    func testShareFromSafari() throws {
        let safari = XCUIApplication(bundleIdentifier: "com.apple.mobilesafari")
        safari.activate()
        XCTAssertTrue(safari.wait(for: .runningForeground, timeout: 20))
        sleep(4) // let the page settle

        // 0. First-run tips cover the toolbar on a fresh simulator
        for _ in 0..<2 { let close = safari.buttons["Close"]; if close.exists { close.tap(); sleep(1) } }

        // 1. Share button: direct on older iOS; inside the "More" menu on iOS 26
        if let share = [safari.buttons["Share"], safari.buttons["ShareButton"]].first(where: { $0.waitForExistence(timeout: 2) }) {
            share.tap()
        } else if safari.buttons["MoreMenuButton"].waitForExistence(timeout: 3) {
            safari.buttons["MoreMenuButton"].tap()
            sleep(1)
            dump(safari, "more-menu")
            let inMenu = safari.descendants(matching: .any).matching(NSPredicate(format: "label BEGINSWITH 'Share'")).firstMatch
            guard inMenu.waitForExistence(timeout: 5) else { dump(safari, "no-share-in-menu"); XCTFail("no Share in More menu"); return }
            inMenu.tap()
        } else {
            dump(safari, "no-share-button"); XCTFail("no Share button"); return
        }
        sleep(2)

        // 2. Our action in the share sheet (may need scrolling; may sit under "Edit Actions…")
        var target: XCUIElement?
        for attempt in 0..<6 {
            let candidates = [safari.buttons[actionName], safari.cells[actionName],
                              safari.staticTexts[actionName], safari.otherElements[actionName]]
            if let c = candidates.first(where: { $0.exists }) { target = c; break }
            // also try the share-extension name
            let alt = [safari.buttons["RetAIn (share)"], safari.cells["RetAIn (share)"], safari.staticTexts["RetAIn (share)"]]
            if let c = alt.first(where: { $0.exists }) { target = c; break }
            if attempt == 0 { dump(safari, "share-sheet-open") }
            safari.swipeUp()
            sleep(1)
        }
        guard let target else { dump(safari, "action-not-found"); shot(safari, "action-not-found"); XCTFail("\(actionName) not in share sheet"); return }
        shot(safari, "share-sheet-found")
        target.tap()

        // 3. Wait for the sheet to finish (footer shows "words long") or fail
        let ok = safari.staticTexts.matching(NSPredicate(format: "label CONTAINS 'words long'")).firstMatch
        let bad = safari.staticTexts.matching(NSPredicate(format: "label CONTAINS[c] 'transform this'")).firstMatch
        let t0 = Date()
        while Date().timeIntervalSince(t0) < 180 {
            if ok.exists || bad.exists { break }
            sleep(2)
        }
        // reveal the debug summary in the footer, then screenshot
        if safari.buttons["Debug"].exists { safari.buttons["Debug"].tap(); sleep(1) }
        shot(safari, "sheet-result")
        dump(safari, "sheet-result")
        XCTAssertTrue(ok.exists, bad.exists ? "sheet failed: \(bad.label)" : "sheet never finished")
        sleep(3)
    }

    private func shot(_ app: XCUIApplication, _ name: String) {
        let data = app.screenshot().pngRepresentation
        try? data.write(to: URL(fileURLWithPath: outDir).appendingPathComponent("\(name).png"))
    }
    private func dump(_ app: XCUIApplication, _ name: String) {
        try? app.debugDescription.write(to: URL(fileURLWithPath: outDir).appendingPathComponent("\(name).txt"), atomically: true, encoding: .utf8)
    }
}
