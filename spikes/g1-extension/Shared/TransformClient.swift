import Foundation

enum TransformError: LocalizedError {
    case server(String)
    var errorDescription: String? { if case .server(let s) = self { return s }; return nil }
}

/// Talks to the PoC server (src/serve.py): POST /api/transform → id, then GET /api/rewrite?id → piece.
/// The rewrite call blocks until generation + QC finish (D29: nothing QC-touched reaches the screen),
/// so "streaming" in the sheet means: a spinner that survives a 10–30 s request.
enum TransformClient {
    static var base: URL {
        let s = (Bundle.main.object(forInfoDictionaryKey: "RETAIN_SERVER") as? String) ?? "http://127.0.0.1:8484"
        return URL(string: s)!
    }

    private struct Created: Decodable { let id: String; let read_url: String }
    private struct Raw: Decodable { let title: String; let body: String; let label: String; let attrib: String }
    private struct Err: Decodable { let error: String }

    static func transform(text: String, title: String?, url: String?, source: String) async throws -> Piece {
        let t0 = Date()
        var req = URLRequest(url: base.appending(path: "api/transform"))
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: [
            "text": text, "title": title ?? "", "url": url ?? "", "source": source])
        let (d1, _) = try await URLSession.shared.data(for: req)
        if let e = try? JSONDecoder().decode(Err.self, from: d1) { throw TransformError.server(e.error) }
        let created = try JSONDecoder().decode(Created.self, from: d1)

        var req2 = URLRequest(url: base.appending(path: "api/rewrite")
            .appending(queryItems: [URLQueryItem(name: "id", value: created.id)]))
        req2.timeoutInterval = 240
        let (d2, _) = try await URLSession.shared.data(for: req2)
        if let e = try? JSONDecoder().decode(Err.self, from: d2) { throw TransformError.server(e.error) }
        let raw = try JSONDecoder().decode(Raw.self, from: d2)
        return Piece(id: created.id, title: raw.title, body: raw.body, label: raw.label,
                     attrib: raw.attrib, source: source, created: Date(),
                     latencyMs: Int(Date().timeIntervalSince(t0) * 1000))
    }
}
