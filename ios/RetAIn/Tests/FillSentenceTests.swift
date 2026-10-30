import SwiftUI
import XCTest
@testable import RetAIn

/// The fill-in gap (D65) renders as a real view at any wrap point: the sentence that lost its gap at a
/// line end on the phone ("…increasingly / as the storm…") is drawn at several widths and in each gap
/// state; PNGs go to /tmp/retain-fill-gap/ for a look by eye.
@MainActor
final class FillSentenceTests: XCTestCase {
    private let out = URL(fileURLWithPath: "/tmp/retain-fill-gap")
    private let precarious = "The hiker realized her position on the crumbling ledge was increasingly _____ as the storm clouds began to gather overhead."

    func testGapRendersAtEveryWrapPoint() throws {
        try? FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
        let states: [(String, FillSentence.Gap)] = [("empty", .typing("")), ("typing", .typing("prec")),
                                                    ("wrong", .wrong("perilous")), ("solved", .solved("precarious"))]
        for width in [300, 330, 350, 370] as [CGFloat] {
            for (name, gap) in states {
                let view = FillSentence(text: precarious, letters: 10, gap: gap)
                    .frame(width: width, alignment: .leading).padding().background(.white)
                let renderer = ImageRenderer(content: view)
                renderer.scale = 2
                let png = try XCTUnwrap(renderer.uiImage?.pngData(), "\(name) at \(width) didn't render")
                try png.write(to: out.appending(path: "\(Int(width))-\(name).png"))
            }
        }
    }

    func testFillDecodesLetterCount() throws {
        let json = #"{"text": "She remained _____.", "source": "model", "letters": 7}"#
        XCTAssertEqual(try JSONDecoder().decode(PracticeItem.Fill.self, from: Data(json.utf8)).letters, 7)
        let old = #"{"text": "She remained _____.", "source": "model"}"#  // a server from before D65
        XCTAssertNil(try JSONDecoder().decode(PracticeItem.Fill.self, from: Data(old.utf8)).letters)
    }
}
