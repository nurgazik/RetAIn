import XCTest
@testable import RetAIn

/// Runs against the local service (http://127.0.0.1:8585) with the dev token from the
/// RETAIN_DEV_TOKEN test-runner environment variable. Skips when it isn't set.
final class RetAInClientTests: XCTestCase {
    override func setUpWithError() throws {
        guard let t = ProcessInfo.processInfo.environment["RETAIN_DEV_TOKEN"], !t.isEmpty else {
            throw XCTSkip("RETAIN_DEV_TOKEN not set")
        }
        SessionStore.setServerURL("http://127.0.0.1:8585")
        SessionStore.token = t
    }

    func testMeAndWords() async throws {
        let me = try await RetAInClient.shared.me()
        XCTAssertGreaterThan(me.learningWords, 0)
        let words = try await RetAInClient.shared.words()
        XCTAssertEqual(words.filter { $0.status == "learning" }.count, me.learningWords)
    }

    /// D59: set and clear a note, then put back whatever note the word had (a real account).
    func testNoteRoundTrips() async throws {
        let words = try await RetAInClient.shared.words()
        let w = try XCTUnwrap(words.first)
        let set = try await RetAInClient.shared.setNote(w.id, "  перевод — test note  ")
        XCTAssertEqual(set.note, "перевод — test note")
        let listed = try await RetAInClient.shared.words().first { $0.id == w.id }
        XCTAssertEqual(listed?.note, "перевод — test note")
        let cleared = try await RetAInClient.shared.setNote(w.id, "")
        XCTAssertNil(cleared.note)
        _ = try await RetAInClient.shared.setNote(w.id, w.note ?? "")
    }

    func testTransformStreamsPhasesThenPiece() async throws {
        let accepted = try await RetAInClient.shared.transform(text: Sample.text, title: "Test", url: nil, source: "unit-test")
        var phases: [String] = []
        var piece: Piece?
        for try await ev in try RetAInClient.shared.events(pieceId: accepted.pieceId) {
            switch ev {
            case .phase(let p): phases.append(p)
            case .piece(let p): piece = p
            case .error(let e): XCTFail(e)
            }
        }
        XCTAssertTrue(phases.contains("generating"), "phases: \(phases)")
        XCTAssertEqual(phases.last, "done")
        let p = try XCTUnwrap(piece)
        XCTAssertEqual(p.status, "done")
        XCTAssertNotNil(p.bodyHtml)
        try await RetAInClient.shared.tap(pieceId: p.id, word: p.wordsUsed?.first ?? "bolster")
        let list = try await RetAInClient.shared.pieces()
        XCTAssertTrue(list.contains { $0.id == p.id })
    }
}

/// A sample post for the live transform test (it lived in the paste tab, removed by D64).
private enum Sample {
    static let text = """
    I've been at my company for about two years and things are mostly fine, but my manager has cancelled or moved our one-on-one six times in the last two months. Every time it's a last-minute message: sorry, something came up, let's do next week. Next week it happens again.

    I don't think she's doing it on purpose. She got two more direct reports in the spring and her calendar is a disaster. But the effect on me is real. I have a promotion case I want to build and I can't get twenty minutes to talk about it. Small decisions that need her sign-off are stalling.

    What I've tried: I sent a short agenda ahead of the last two meetings so she'd see there was something concrete. Didn't help. I asked if a different day would work better. She said Thursdays, then cancelled Thursday.

    How do I bring this up without sounding like I'm complaining about her workload, which she can't change?
    """
}
