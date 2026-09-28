import AVFoundation
import SwiftUI

/// A word's card (D48): meanings in Wiktionary's order with the model's examples, the IPA and
/// a speak button, badges for AI-written and unverified words, credits. Used by the word list,
/// the capture screen and the reader's bottom sheet.
struct WordCardView: View {
    let word: Word
    /// Status buttons ("Got it — mark retained", "Archive"); nil hides them (capture screen).
    var onStatus: ((String) -> Void)? = nil

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                header
                if word.isUnverified {
                    Label("Not found in the dictionary. Check the spelling, or archive it.", systemImage: "questionmark.circle")
                        .font(.callout).foregroundStyle(.secondary)
                }
                if let card = word.card {
                    ForEach(Array(card.senses.enumerated()), id: \.offset) { i, s in sense(i + 1, s) }
                } else if !word.definition.isEmpty {
                    Text(word.definition).font(.body)
                }
                if let n = word.servings { Text("Seen in \(n) read\(n == 1 ? "" : "s")").font(.caption).foregroundStyle(.secondary) }
                actions
                credits
            }
            .padding()
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(alignment: .firstTextBaseline) {
                Text(word.card?.headword ?? word.word).font(.title.weight(.semibold))
                if let h = word.card?.headword, h != word.word { Text("from “\(word.word)”").font(.subheadline).foregroundStyle(.secondary) }
                Spacer()
                Text(word.status).font(.caption).padding(.horizontal, 8).padding(.vertical, 3).background(.thinMaterial, in: Capsule())
            }
            HStack(spacing: 8) {
                if let ipa = word.card?.ipa, !ipa.isEmpty {
                    Text(ipa.map(\.ipa).joined(separator: "  ")).font(.callout).foregroundStyle(.secondary)
                }
                if !word.isUnverified {
                    Button { Speech.say(word.card?.headword ?? word.word) } label: { Image(systemName: "speaker.wave.2") }
                        .buttonStyle(.borderless).accessibilityLabel("Pronounce")
                }
                if word.card?.source == "model" { badge("Written by AI") }
                if word.isUnverified { badge("Unverified") }
            }
        }
    }

    private func sense(_ n: Int, _ s: Card.Sense) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Text("\(n).").font(.body.monospacedDigit()).foregroundStyle(.secondary)
                VStack(alignment: .leading, spacing: 4) {
                    let labels = s.tags.filter { !Self.noiseTags.contains($0) }
                    if s.pos != nil || !labels.isEmpty {
                        Text(([s.pos].compactMap { $0 } + labels).joined(separator: " · "))
                            .font(.caption.smallCaps()).foregroundStyle(.tint)
                    }
                    Text(s.gloss).font(.body)
                    ForEach(s.examples, id: \.self) { Text("“\($0)”").font(.callout.italic()).foregroundStyle(.secondary) }
                }
            }
        }
    }

    @ViewBuilder private var actions: some View {
        if let onStatus {
            if word.isUnverified, word.status != "archived" {
                Button("Archive") { onStatus("archived") }.buttonStyle(.bordered)
            } else if word.status == "learning" {
                Button("Got it — mark retained") { onStatus("retained") }.buttonStyle(.borderedProminent)
            }
        }
    }

    @ViewBuilder private var credits: some View {
        if let card = word.card {
            VStack(alignment: .leading, spacing: 2) {
                if card.source == "wiktionary", let s = card.sourceUrl, let url = URL(string: s) {
                    Link("Source: Wiktionary (CC BY-SA 4.0)", destination: url)
                }
                if card.senses.contains(where: { !$0.examples.isEmpty }) { Text("Examples written by AI") }
            }
            .font(.caption2).foregroundStyle(.secondary).padding(.top, 6)
        }
    }

    private func badge(_ s: String) -> some View {
        Text(s).font(.caption2.weight(.medium)).padding(.horizontal, 6).padding(.vertical, 2)
            .background(.orange.opacity(0.18), in: Capsule())
    }

    /// Wiktionary qualifiers that read as noise on a card ("also", "usually"…).
    private static let noiseTags: Set<String> = ["also", "usually", "specifically", "broadly", "form-of", "with", "often", "sometimes"]
}

/// Apple's on-device speech for the speak button: free, offline, no per-recording credits (D48).
enum Speech {
    private static let synth = AVSpeechSynthesizer()
    static func say(_ text: String) {
        let u = AVSpeechUtterance(string: text)
        u.voice = AVSpeechSynthesisVoice(language: "en-US")
        synth.stopSpeaking(at: .immediate)
        synth.speak(u)
    }
}
