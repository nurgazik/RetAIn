import Foundation

/// Local cache of finished pieces in the app-group container, so My Reads opens offline
/// and a piece made in an extension is visible to the app at once.
enum ReadsStore {
    private static var file: URL {
        (FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: SessionStore.appGroup)
         ?? FileManager.default.temporaryDirectory).appending(path: "reads.json")
    }
    static func load() -> [Piece] {
        guard let d = try? Data(contentsOf: file) else { return [] }
        return (try? JSONDecoder().decode([Piece].self, from: d)) ?? []
    }
    static func save(_ p: Piece) {
        var all = load()
        all.removeAll { $0.id == p.id }
        all.insert(p, at: 0)
        try? JSONEncoder().encode(Array(all.prefix(200))).write(to: file, options: .atomic)
    }
    static func replaceAll(_ pieces: [Piece]) {
        try? JSONEncoder().encode(Array(pieces.prefix(200))).write(to: file, options: .atomic)
    }
}
