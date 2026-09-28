import Foundation

/// Local copy of the word list in the app-group container, so the home-screen widget can
/// show words without calling the server. The app refreshes it on every words load.
/// Also picks the widget's words of the day and remembers which one it is showing.
enum WordsStore {
    static let perDay = 5
    private static var file: URL {
        (FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: SessionStore.appGroup)
         ?? FileManager.default.temporaryDirectory).appending(path: "words.json")
    }
    /// nil when the app has never saved a list (signed out, or not opened since install).
    static func load() -> [Word]? {
        guard let d = try? Data(contentsOf: file) else { return nil }
        return try? JSONDecoder().decode([Word].self, from: d)
    }
    static func replaceAll(_ words: [Word]) {
        try? JSONEncoder().encode(words).write(to: file, options: .atomic)
    }

    /// Up to `perDay` learning words, the same set all day, a new set each local day.
    static func todaysWords(from words: [Word], day: String) -> [Word] {
        var rng = SeededRNG(seed: day)
        let learning = words.filter { $0.status == "learning" }.sorted { $0.id < $1.id }
        return Array(learning.shuffled(using: &rng).prefix(perDay))
    }
    static func dayKey(_ date: Date = .now) -> String {
        let f = DateFormatter(); f.calendar = Calendar(identifier: .gregorian)
        f.locale = Locale(identifier: "en_US_POSIX"); f.timeZone = .current; f.dateFormat = "yyyy-MM-dd"
        return f.string(from: date)
    }

    // Widget position within today's words; resets when the day changes.
    static func position(day: String) -> Int {
        SessionStore.defaults.string(forKey: "widgetDay") == day ? SessionStore.defaults.integer(forKey: "widgetIndex") : 0
    }
    static func advance(day: String, count: Int) {
        guard count > 0 else { return }
        SessionStore.defaults.set(day, forKey: "widgetDay")
        SessionStore.defaults.set((position(day: day) + 1) % count, forKey: "widgetIndex")
    }
}

/// SplitMix64 seeded from a string, so a shuffle is repeatable (Swift has no seeded RNG).
struct SeededRNG: RandomNumberGenerator {
    private var state: UInt64
    init(seed: String) {
        state = seed.utf8.reduce(14695981039346656037) { ($0 ^ UInt64($1)) &* 1099511628211 }  // FNV-1a
    }
    mutating func next() -> UInt64 {
        state &+= 0x9E3779B97F4A7C15
        var z = state
        z = (z ^ (z >> 30)) &* 0xBF58476D1CE4E5B9
        z = (z ^ (z >> 27)) &* 0x94D049BB133111EB
        return z ^ (z >> 31)
    }
}
