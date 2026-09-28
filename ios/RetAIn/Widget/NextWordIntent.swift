import AppIntents
import WidgetKit

/// The widget's › button: move to the next of today's words (wraps after the last).
struct NextWordIntent: AppIntent {
    static var title: LocalizedStringResource = "Next word"
    func perform() async throws -> some IntentResult {
        let day = WordsStore.dayKey()
        let count = WordsStore.todaysWords(from: WordsStore.load() ?? [], day: day).count
        WordsStore.advance(day: day, count: count)
        return .result()
    }
}
