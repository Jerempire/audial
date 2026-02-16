// Preset songs — atmospheric/ambient compositions for art and historical projects
export interface Preset {
  name: string;
  tags: string[];
  code: string;
}

export const PRESETS: Preset[] = [
  {
    name: "Medieval Cathedral",
    tags: ["dark", "sacred", "slow"],
    code: `setcpm(50)

// organ drone - deep cathedral foundation
$: note("<[d2,a2,d3] [c2,g2,c3] [bb1,f2,bb2] [c2,g2,c3]>")
  .s("sawtooth")
  .lpf(400)
  .gain(0.25)
  .slow(4)
  .room(0.8)

// high overtones - light through stained glass
$: note("d5 ~ ~ a5 ~ ~ f5 ~ ~ g5 ~ ~")
  .s("sine")
  .gain(0.1)
  .delay(0.5)
  .room(0.9)
  .slow(3)

// bell - distant tower
$: note("d6 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~")
  .s("sine")
  .gain(0.08)
  .room(0.95)
  .delay(0.7)
  .slow(4)

// sub bass - stone floor resonance
$: note("d2 ~ ~ ~ c2 ~ ~ ~ bb1 ~ ~ ~ c2 ~ ~ ~")
  .s("sine")
  .lpf(120)
  .gain(0.3)
  .slow(4)`,
  },
  {
    name: "Ancient Ruins",
    tags: ["mysterious", "sparse", "ambient"],
    code: `setcpm(40)

// wind drone - open desert air
$: note("<[e3,b3] [d3,a3] [e3,b3] [f#3,c#4]>")
  .s("sawtooth")
  .lpf(600)
  .gain(0.15)
  .slow(4)
  .room(0.7)

// metallic resonance - ancient bronze
$: note("e5 ~ ~ ~ ~ b5 ~ ~ ~ ~ g5 ~ ~ ~ ~ ~")
  .s("triangle")
  .gain(0.08)
  .delay(0.6)
  .room(0.85)
  .slow(3)

// sparse percussion - sand and stone
$: s("~ ~ hh ~ ~ ~ hh ~ ~ ~ ~ ~ ~ hh ~ ~")
  .gain(0.12)
  .lpf(3000)
  .room(0.6)
  .slow(2)

// deep earth hum
$: note("e2")
  .s("sine")
  .lpf(100)
  .gain(0.2)
  .slow(8)`,
  },
  {
    name: "Renaissance Court",
    tags: ["warm", "elegant", "flowing"],
    code: `setcpm(72)

// plucked strings - courtly dance
$: note("[g4 b4 d5] [a4 c5 e5] [f#4 a4 d5] [g4 b4 d5]")
  .s("triangle")
  .gain(0.2)
  .delay(0.2)
  .room(0.4)
  .slow(2)

// bass movement - stately procession
$: note("g3 ~ d3 ~ a3 ~ d3 ~ f#3 ~ d3 ~ g3 ~ d3 ~")
  .s("sawtooth")
  .lpf(500)
  .gain(0.25)
  .slow(2)

// melodic ornament - flute-like
$: note("~ d5 ~ g5 ~ b5 ~ a5 ~ ~ d5 ~ f#5 ~ ~ ~")
  .s("sine")
  .gain(0.12)
  .delay(0.3)
  .room(0.5)
  .slow(2)

// gentle pulse
$: s("~ ~ bd ~ ~ ~ ~ ~")
  .gain(0.15)
  .lpf(200)
  .room(0.3)`,
  },
  {
    name: "Gothic Horror",
    tags: ["dark", "tense", "dissonant"],
    code: `setcpm(55)

// dissonant cluster - dread
$: note("<[c3,f#3,b3] [db3,g3,c4] [c3,gb3,bb3] [d3,ab3,c4]>")
  .s("sawtooth")
  .lpf(700)
  .gain(0.2)
  .slow(4)
  .room(0.85)

// creaking texture - high tension
$: note("b5 ~ c6 ~ ~ ~ bb5 ~ ~ ~ c6 ~ ~ ~ ~ ~")
  .s("square")
  .lpf(2000)
  .gain(0.06)
  .delay(0.7)
  .room(0.9)
  .slow(3)

// heartbeat - sub bass pulse
$: s("bd ~ ~ ~ ~ bd ~ ~ ~ ~ ~ ~ ~ bd ~ ~")
  .gain(0.3)
  .lpf(80)
  .room(0.4)
  .slow(2)

// distant screech
$: note("~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ c7")
  .s("sawtooth")
  .lpf(6000)
  .hpf(2000)
  .gain(0.04)
  .delay(0.8)
  .room(0.95)
  .slow(8)`,
  },
  {
    name: "Impressionist Garden",
    tags: ["bright", "gentle", "warm"],
    code: `setcpm(80)

// soft arpeggios - sunlight on water
$: note("[c4 e4 g4 b4] [d4 f4 a4 c5] [e4 g4 b4 d5] [f4 a4 c5 e5]")
  .s("sine")
  .gain(0.15)
  .delay(0.3)
  .room(0.5)
  .slow(2)

// warm pad - garden air
$: note("<[c3,e3,g3,b3] [d3,f3,a3,c4] [e3,g3,b3] [f3,a3,c4]>")
  .s("sawtooth")
  .lpf(900)
  .gain(0.18)
  .slow(4)
  .room(0.4)

// melody fragments - birdsong inspired
$: note("~ g5 ~ ~ e5 ~ ~ ~ b5 ~ ~ ~ c5 ~ ~ ~")
  .s("sine")
  .gain(0.1)
  .delay(0.4)
  .room(0.6)
  .slow(2)

// bass - earth and roots
$: note("c3 ~ ~ ~ d3 ~ ~ ~ e3 ~ ~ ~ f3 ~ ~ ~")
  .s("sine")
  .lpf(250)
  .gain(0.2)
  .slow(4)`,
  },
  {
    name: "War Drums",
    tags: ["intense", "rhythmic", "epic"],
    code: `setcpm(100)

// war drums - tribal pattern
$: s("bd bd ~ bd ~ bd bd ~ bd ~ ~ bd ~ bd bd ~")
  .gain(0.4)
  .lpf(200)
  .room(0.3)

// snare rolls - battle tension
$: s("~ ~ ~ ~ sn ~ ~ sn ~ ~ sn ~ ~ ~ sn:2 ~")
  .gain(0.25)
  .lpf(4000)
  .room(0.2)

// horn call - brass-like synth
$: note("<[d4,a4] ~ ~ ~ [c4,g4] ~ ~ ~ [d4,a4] ~ [e4,b4] ~ [d4,a4] ~ ~ ~>")
  .s("sawtooth")
  .lpf(1200)
  .gain(0.2)
  .slow(2)
  .room(0.4)

// sub bass - ground shaking
$: note("d2 ~ d2 ~ ~ d2 ~ ~ d2 ~ ~ ~ d2 d2 ~ ~")
  .s("sine")
  .lpf(80)
  .gain(0.35)

// cymbal crashes - impact
$: s("~ ~ ~ ~ ~ ~ ~ oh ~ ~ ~ ~ ~ ~ ~ ~")
  .gain(0.15)
  .lpf(6000)
  .room(0.5)`,
  },
];
