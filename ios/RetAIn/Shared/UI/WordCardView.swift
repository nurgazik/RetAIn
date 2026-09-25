import SwiftUI

struct WordCardView: View {
    let word: Word
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .firstTextBaseline) {
                Text(word.word).font(.title.weight(.semibold))
                if let pos = word.pos { Text(pos).font(.subheadline).foregroundStyle(.secondary) }
                Spacer()
                Text(word.status).font(.caption).padding(.horizontal, 8).padding(.vertical, 3)
                    .background(.thinMaterial, in: Capsule())
            }
            Text(word.definition).font(.body)
            if let n = word.servings { Text("Seen in \(n) read\(n == 1 ? "" : "s")").font(.caption).foregroundStyle(.secondary) }
        }
        .padding()
    }
}
