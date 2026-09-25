import Foundation

/// Minimal text/event-stream parser over URLSession's byte stream.
/// Yields (event, data) pairs; comment lines (": ping") are skipped.
struct SSEReader {
    static func events(for request: URLRequest, session: URLSession = .shared)
        -> AsyncThrowingStream<(event: String, data: String), Error> {
        AsyncThrowingStream { continuation in
            let task = Task {
                do {
                    let (bytes, response) = try await session.bytes(for: request)
                    if let http = response as? HTTPURLResponse, http.statusCode >= 400 {
                        throw APIError.http(http.statusCode, "event stream refused")
                    }
                    // AsyncLineSequence skips blank lines, so the blank-line event boundary never
                    // arrives; flush the pending event whenever the next `event:` line (or a
                    // comment/keep-alive) shows up instead.
                    var event = "message", data: [String] = []
                    func flush() {
                        if !data.isEmpty { continuation.yield((event, data.joined(separator: "\n"))) }
                        event = "message"; data = []
                    }
                    for try await line in bytes.lines {
                        if line.isEmpty || line.hasPrefix(":") {
                            flush()
                        } else if line.hasPrefix("event:") {
                            flush()
                            event = line.dropFirst(6).trimmingCharacters(in: .whitespaces)
                        } else if line.hasPrefix("data:") {
                            data.append(String(line.dropFirst(5).trimmingCharacters(in: .whitespaces)))
                        }
                    }
                    flush()
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
            continuation.onTermination = { _ in task.cancel() }
        }
    }
}
