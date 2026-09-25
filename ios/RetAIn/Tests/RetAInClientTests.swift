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
