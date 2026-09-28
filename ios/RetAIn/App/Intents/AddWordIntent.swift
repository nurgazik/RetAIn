import AppIntents
import SwiftUI
import WidgetKit

/// "Hey Siri, add a word to RetAIn" → "Which word?" (D50). Siri can't take an open-ended word in
/// the trigger phrase itself, so it asks for it. Same server call as the share sheet's capture.
struct AddWordIntent: AppIntent {
    static var title: LocalizedStringResource = "Add Word"
    static var description = IntentDescription("Capture a word to retain.")

    @Parameter(title: "Word", requestValueDialog: "Which word?")
    var word: String

    func perform() async throws -> some IntentResult & ProvidesDialog & ShowsSnippetView {
        guard let w = WordInput.normalize(word) else { throw $word.needsValueError("Just one word, please. Which word?") }
        let saved: Word
        do { saved = try await RetAInClient.shared.addWord(w) }
        catch APIError.noSession { throw AddWordError.signedOut }
        catch { throw AddWordError.failed(error.localizedDescription) }
        // Same refresh as the word list, so the widget sees the new word now.
        if let all = try? await RetAInClient.shared.words() {
            WordsStore.replaceAll(all); WidgetCenter.shared.reloadAllTimelines()
        }
        // Siri may have misheard: the server's unverified flag is the spelling check.
        let dialog: IntentDialog = saved.isUnverified
            ? "Saved \(saved.word), but I couldn't find it in the dictionary. Check the spelling."
            : "Added \(saved.word)."
        return .result(dialog: dialog, view: AddedWordSnippet(word: saved))
    }
}

enum AddWordError: Error, CustomLocalizedStringResourceConvertible {
    case signedOut, failed(String)
    var localizedStringResource: LocalizedStringResource {
        switch self {
        case .signedOut: return "Open RetAIn once to sign in."
        case .failed(let m): return "Couldn't add the word: \(m)"
        }
    }
}

/// Siri's result card: the spelling as saved and its first meaning. The full card lives in the app.
private struct AddedWordSnippet: View {
    let word: Word
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(word.card?.headword ?? word.word).font(.title2.weight(.semibold))
            if word.isUnverified {
                Label("Not found in the dictionary", systemImage: "questionmark.circle").font(.callout).foregroundStyle(.orange)
            } else if !word.firstDefinition.isEmpty {
                Text(word.firstDefinition).font(.callout).foregroundStyle(.secondary).lineLimit(3)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
    }
}
