import SwiftUI
import XCTest
@testable import RetAIn

/// The sentence check's fix with its changes marked (2026-11-16). PNGs go to $SHOTS_DIR/retain-marked-fix.
@MainActor
final class SentenceDiffTests: XCTestCase {
    private func marks(_ a: String, _ b: String) -> [String]? {
        SentenceDiff.pieces(from: a, to: b)?.compactMap { p in
            switch p.kind {
            case .same: nil
            case .added: "+" + p.text.trimmingCharacters(in: .whitespaces)
            case .removed: "-" + p.text.trimmingCharacters(in: .whitespaces)
            }
        }
    }

    func testACommaAndAnArticleAreTheOnlyMarks() {
        XCTAssertEqual(marks("Despite adversity she faced she kept going.", "Despite the adversity she faced, she kept going."),
                       ["+the", "+,"])
    }

    func testAReplacedWordShowsTheOldThenTheNew() {
        XCTAssertEqual(marks("Despite a adversity, she kept going.", "Despite the adversity, she kept going."),
                       ["-a", "+the"])
        XCTAssertEqual(marks("she kept going", "She kept going."), ["-she", "+She", "+."])   // a capital counts
    }

    func testSpacesAndApostrophesAreNotEdits() {
        XCTAssertEqual(marks("It's  a well-known   fact.", "It's a well-known fact."), [])
    }

    func testTheReadingOrderKeepsTheFixedSentence() {
        let p = SentenceDiff.pieces(from: "She felt ambivalence about the move.", to: "She felt ambivalent about the move.")!
        XCTAssertEqual(p.filter { $0.kind != .removed }.map(\.text).joined(), "She felt ambivalent about the move.")
    }

    func testARewriteHasNoMarks() {
        XCTAssertNil(SentenceDiff.pieces(from: "The adversity was big for me in school.",
                                         to: "She faced great adversity during her school years."))
    }

    func testRendersForALook() throws {
        let dir = URL(fileURLWithPath: ProcessInfo.processInfo.environment["SHOTS_DIR"] ?? NSTemporaryDirectory())
            .appending(path: "retain-marked-fix")
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let cases = [("polished", "Despite adversity she faced in her first year abroad she kept going.",
                      "Despite the adversity she faced in her first year abroad, she kept going."),
                     ("replaced", "He showed great ambivalence for the new plan, and a acceptance later.",
                      "He showed great ambivalence about the new plan, and an acceptance later."),
                     ("rewrite", "The adversity was big for me in school.", "She faced great adversity during her school years.")]
        for (name, mine, fixed) in cases {
            let view = VStack(alignment: .leading, spacing: 8) {
                Text("Polished:").font(.callout).bold()
                MarkedFix(mine: mine, fixed: fixed)
            }
            .frame(width: 340, alignment: .leading).padding().background(Color.paper)
            for (scheme, tag) in [(ColorScheme.light, ""), (.dark, "-dark")] {
                let r = ImageRenderer(content: view.environment(\.colorScheme, scheme)); r.scale = 3
                try XCTUnwrap(r.uiImage?.pngData()).write(to: dir.appending(path: "\(name)\(tag).png"))
            }
        }
    }
}
