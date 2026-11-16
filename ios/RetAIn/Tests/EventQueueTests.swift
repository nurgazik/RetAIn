import XCTest
@testable import RetAIn

/// D74: the event queue keeps each event as its own file until the server has answered for it.
final class EventQueueTests: XCTestCase {
    private var dir: URL!

    override func setUp() {
        dir = FileManager.default.temporaryDirectory.appending(path: "events-\(UUID().uuidString)")
    }
    override func tearDown() { try? FileManager.default.removeItem(at: dir) }

    private func event(_ kind: String = "open", at: Date = Date()) -> EventQueue.Event {
        let f = ISO8601DateFormatter(); f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return .init(id: EventQueue.newId(), kind: kind, surface: "reader", at: f.string(from: at), pieceId: "p_1")
    }

    func testSentEventsLeaveTheQueueInOrder() async throws {
        let sent = Box()
        let q = EventQueue(dir: dir, send: { await sent.append($0) })
        let a = event(at: Date().addingTimeInterval(-60)), b = event("tap")
        await q.add(b); await q.add(a)
        await q.flush()
        let batches = await sent.batches
        XCTAssertEqual(batches, [[a, b]], "oldest first, one batch")
        let left = await q.pending()
        XCTAssertTrue(left.isEmpty)
    }

    func testANetworkFailureKeepsEverythingForNextTime() async throws {
        let q = EventQueue(dir: dir, send: { _ in throw URLError(.notConnectedToInternet) })
        await q.add(event()); await q.add(event())
        await q.flush()
        let left = await q.pending()
        XCTAssertEqual(left.count, 2)
    }

    func testABatchTheServerRefusesIsDroppedNotRetriedForever() async throws {
        let q = EventQueue(dir: dir, send: { _ in throw APIError.http(422, "bad") })
        await q.add(event())
        await q.flush()
        let left = await q.pending()
        XCTAssertTrue(left.isEmpty)
    }

    func testSignedOutKeepsTheQueue() async throws {
        let q = EventQueue(dir: dir, send: { _ in throw APIError.http(401, "no session") })
        await q.add(event())
        await q.flush()
        let left = await q.pending()
        XCTAssertEqual(left.count, 1)
    }

    /// The app and an extension each have their own queue object on the same folder: one send takes both.
    func testTwoProcessesShareOneFolder() async throws {
        let sent = Box()
        let app = EventQueue(dir: dir, send: { await sent.append($0) })
        let ext = EventQueue(dir: dir, send: { _ in throw URLError(.timedOut) })
        await ext.add(event()); await app.add(event("tap"))
        await app.flush()
        let n = await sent.batches.first?.count
        XCTAssertEqual(n, 2)
    }

    func testEventsOlderThanThreeDaysAreDropped() async throws {
        let q = EventQueue(dir: dir, send: { _ in })
        await q.add(event(at: Date().addingTimeInterval(-4 * 86_400)))
        let left = await q.pending()
        XCTAssertTrue(left.isEmpty)
    }

    actor Box {
        var batches: [[EventQueue.Event]] = []
        func append(_ b: [EventQueue.Event]) { batches.append(b) }
    }
}
