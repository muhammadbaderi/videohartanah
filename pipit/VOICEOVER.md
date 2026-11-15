# Voiceover script (Bahasa Melayu santai)

Voice: ElevenLabs **"Suara sendiri (videohartanah)"** (`graVYRgsElnbev50WXQ2`), the owner's own
cloned voice from the Meru site-visit video. Generated in one take so the delivery flows, with v3
audio tags for energy (the owner asked for it not to be monotone). Numbers and acronyms are written
the way they should be said. The screen never shows the same sentence word for word.

| Scene | What the screen shows | What the voice says |
|---|---|---|
| s1-hook | RUMAH BERKEMBAR 1-TINGKAT · Jalan Pipit · DARI RM485,700 | Rumah berkembar setingkat, kat Telok Panglima Garang... dah buka pendaftaran! |
| s2-unit | HANYA 8 UNIT SAHAJA | Tapi jangan tunggu lama, lapan unit je tau! |
| s3-pakej | BOOKING RM1,000 · 3× FREE | Booking? Seribu ringgit je. Legal fee SPA, free. Disbursement, free. Rumah pertama? MOT pun free! |
| s4-pelan | Plan · 4 Bilik & 2 Bilik Air · 2,814 kps · 1,266 kps | Empat bilik, dua bilik air. Tanah dua ribu lapan ratus empat belas kaki persegi, binaan seribu dua ratus enam puluh enam. |
| s5-tapak | LEASEHOLD Rizab Melayu · Dijangka siap Q4 2027 | Leasehold, Rizab Melayu. Dijangka siap hujung tahun dua ribu dua puluh tujuh. |
| s6-peta | Satellite: Jalan Pipit, Shah Alam 23 / KLCC 42 / Putrajaya 41 min, highways | Nak ke Shah Alam? Dua puluh tiga minit. KLCC, empat puluh dua minit. SKVE, KESAS, WCE, semua dekat. |
| s7-dekat | DEKAT DENGAN 5 / 6 / 9 min | Sekolah? Lima minit je. Ninety-nine Speedmart enam minit, Eco Sanctuary sembilan minit. |
| s8-cta | HARGA DARI RM485,700 · Booking RM1,000 · phone | Harga dari empat ratus lapan puluh lima ribu tujuh ratus. Booking seribu je... jom, hubungi saya sekarang! |

"Hujung tahun 2027" is how the voice says the brochure's "Q4 2027" (October to December).
"Semua dekat" stands for the brochure's "Akses mudah" list of highways.

## How it was made (and checked)

- `scripts/pipit/voiceover.py` (ElevenLabs `with-timestamps`, so every word has a time):
  `eleven_v3`, stability 0.5 ("natural"), seed 7, one take of all 8 lines → `assets/audio/voiceover.wav`
  (high-pass 70 Hz, loudness-normalised to -16 LUFS / -1.5 dBTP). Word times: `voiceover-words.json`.
- That take cut off its very last word ("sekarang"), so the closing line was re-voiced alone
  (`--only s8-cta --tail "Terima kasih, jumpa nanti."`, seed 11) and cut in the silence before the
  throwaway tail → `assets/audio/voiceover-end.wav`, matched to the same loudness. Word times:
  `voiceover-end-words.json`.
- Three full takes were compared on pitch movement (Praat), against the owner's own speech in the
  Meru video (2.9 semitones std, 8.5 st range):

  | Take | Length | Pitch std | Pitch range (p5-p95) | Loudness std |
  |---|---|---|---|---|
  | **eleven_v3, natural (used)** | 54.2 s | **4.3 st** | **13.7 st** | 6.2 dB |
  | eleven_v3, creative | 51.5 s | 3.8 st | 12.9 st | 5.3 dB |
  | eleven_multilingual_v2, style 0.55 | 58.0 s | 3.9 st | 11.4 st | 4.9 dB |
  | closing line re-voice (used) | 7.3 s | 4.9 st | 16.7 st | |

- Whisper (medium, Malay) read the used audio back as the script, word for word apart from its own
  spelling ("Teluk", "Lease hole", "ke Syah Alam" heard as "kesia alam"); the re-voiced ending reads
  "Jom hubungi saya sekarang". Nobody has listened to it: these are measurements, not a listen.
