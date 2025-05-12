/** 
* @file config.tsx
* @description This file contains constants used throughout the application.
*/

/**
 * The maximum size dimension allowed for a garden in the application.
 */
const MAXSIZE_GARDEN: number = 10;

/**
 * A list of page names used in the application.
 */
const PAGES: string[] = ['dashboard', 'catalog', 'settings', 'notifications', 'profile'];

/**
 * A list of colors represented in hexadecimal format.
 * These colors can be used for UI theming or other purposes.
 */
const COLORS: string[] = [
    "#FF0000", // red
    "#0000FF", // blue
    "#800080", // purple
    "#FFC0CB", // pink
    "#FFA500", // orange
    "#FFFF00", // yellow
    "#00FFFF", // cyan
    "#FF00FF", // magenta
    "#4B0082", // indigo
    "#EE82EE", // violet
    "#008000"  // green
];

/// The maximum number of plants that can be attached to a notification.
const MAX_PLANTS_NOTIFICATION = 3;

/// The maximum number of characters allowed in a notification name.
const MAX_CHAR_NOTIFICATION = 10;

 /** Ceiling for number of plants in search response */
const MAX_RESPONSE_PLANTS = 30;

/**
 * A mapping of plant families to their corresponding icons.
 * This object provides a fun and quirky way to associate plant families with representative emojis.
 * Each key represents the name of a plant family, and the value is an emoji that symbolizes it.
 */
const ICONS: Record<string, string> = {
    Asteraceae: '🌻', // Daisy family - "Sunflowers are just daisies with big dreams."
    Rosaceae: '🌹', // Rose family - "Stop and smell the roses... or else!"
    Fabaceae: '🥜', // Legume family - "Peas be with you."
    Poaceae: '🎋', // Grass family - "Bamboo is just grass that hit the gym."
    Lamiaceae: '🍃', // Mint family - "Stay cool, it's mint to be."
    Apiaceae: '🥗', // Carrot family - "Lettuce celebrate this family!"
    Brassicaceae: '🥬', // Mustard family - "Kale yeah!"
    Solanaceae: '🍆', // Nightshade family - "Eggplants: the night owls of veggies."
    Cucurbitaceae: '🎃', // Gourd family - "Pumpkin spice and everything nice."
    Rutaceae: '🍊', // Citrus family - "Orange you glad this family exists?"
    Malvaceae: '🍫', // Mallow family - "Marshmallows are their sweet legacy."
    Amaryllidaceae: '🧄', // Amaryllis family - "Garlic: the vampire's kryptonite."
    Orchidaceae: '🦋', // Orchid family - "Orchids: flowers that moonlight as butterflies."
    Pinaceae: '🎄', // Pine family - "Christmas trees: the OG influencers."
    Fagaceae: '🌰', // Beech family - "Nuts about this family!"
    Betulaceae: '🍂', // Birch family - "Fall leaves brought to you by Betulaceae."
    Salicaceae: '🛶', // Willow family - "Willow trees: nature's kayaks."
    Euphorbiaceae: '🧪', // Spurge family - "Careful, they might be plotting something toxic."
    Cactaceae: '🌵', // Cactus family - "Cactus: the introverts of the plant world."
    Lauraceae: '🥑', // Laurel family - "Avocados: guac stars of this family."
    Myrtaceae: '🧼', // Myrtle family - "Smells fresh, like a bar of soap."
    Araceae: '🪴', // Arum family - "Houseplants that know how to party."
    Cyperaceae: '🦩', // Sedge family - "Flamingos love this family. Coincidence?"
    Juncaceae: '🧵', // Rush family - "Rush to weave some baskets!"
    Ranunculaceae: '🐸', // Buttercup family - "Frogs love buttercups. It's science."
    Caryophyllaceae: '💄', // Pink family - "Pretty in pink, always."
    Polygonaceae: '📐', // Knotweed family - "Geometry nerds of the plant world."
    Chenopodiaceae: '🥬', // Goosefoot family - "Spinach: the Popeye-approved member."
    Amaranthaceae: '🌈', // Amaranth family - "Rainbow quinoa, anyone?"
    Arecaceae: '🌴', // Palm family - "Palm trees: the chillest plants ever."
    Bromeliaceae: '🍍', // Bromeliad family - "Pineapples: spiky on the outside, sweet on the inside."
    Zingiberaceae: '🫚', // Ginger family - "Ginger: the spice of life."
    Musaceae: '🍌', // Banana family - "Bananas: the comedians of the fruit world."
    Sapindaceae: '🍁', // Soapberry family - "Maple syrup: the sticky MVP."
    Aceraceae: '🍁', // Maple family - "Canada approves this family."
    Ulmaceae: '🏰', // Elm family - "Elms: the medieval castles of trees."
    Moraceae: '🍇', // Mulberry family - "Mulberries: the underdog of berries."
    Anacardiaceae: '🥭', // Cashew family - "Mangoes and cashews: a dynamic duo."
    Proteaceae: '🦚', // Protea family - "Proteas: the peacocks of flowers."
    Ericaceae: '🫐', // Heath family - "Blueberries: the sweet little rebels."
    Rubiaceae: '☕', // Coffee family - "Powered by caffeine."
    Oleaceae: '🫒', // Olive family - "Olives: the martini's best friend."
    Caprifoliaceae: '🍯', // Honeysuckle family - "Sweet as honey."
    Plantaginaceae: '🏃', // Plantain family - "Plantains: bananas that run marathons."
    Scrophulariaceae: '🧙', // Figwort family - "Figworts: the wizards of the plant kingdom."
    Boraginaceae: '🖋️', // Borage family - "Borage: the calligrapher's favorite."
    Verbenaceae: '🪄', // Verbena family - "Magical and mysterious."
    Acanthaceae: '🐟', // Acanthus family - "Fish love hiding in these plants."
    Gesneriaceae: '🎤', // Gesneriad family - "Singing their way into your heart."
    Campanulaceae: '🔔', // Bellflower family - "Ring the bell for this family!"
    Dipsacaceae: '🪒', // Teasel family - "Teasels: nature's combs."
    Valerianaceae: '💤', // Valerian family - "Valerian: the plant that naps."
    Araliaceae: '🕷️', // Ivy family - "Creeping into your nightmares."
    Cornaceae: '🍒', // Dogwood family - "Dogwoods: cherries' cool cousins."
    Alismataceae: '🛶', // Water-plantain family - "Perfect for a canoe trip."
    Hydrocharitaceae: '🐟', // Frog's-bit family - "Aquatic plants with froggy vibes."
    Nymphaeaceae: '🌸', // Water-lily family - "Water lilies: the Monet muses."
    Magnoliaceae: '🌺', // Magnolia family - "Magnolias: the southern belles."
    Papaveraceae: '🌺', // Poppy family - "Poppies: the dreamers of the plant world."
    Crassulaceae: '🪨', // Stonecrop family - "Succulents: the rock stars."
    Saxifragaceae: '❄️', // Saxifrage family - "Cool as ice."
    Vitaceae: '🍷', // Grape family - "Wine not?"
    Bignoniaceae: '🎺', // Trumpet creeper family - "Blowing their own trumpet."
    Lythraceae: '🕯️', // Loosestrife family - "Lighting up the wetlands."
    Onagraceae: '🌅', // Evening primrose family - "Primroses: the sunset lovers."
    Geraniaceae: '🌺', // Geranium family - "Geraniums: the garden's cheerleaders."
    Oxalidaceae: '☘️', // Wood sorrel family - "Lucky charms!"
    Celastraceae: '🧗', // Bittersweet family - "Climbing to new heights."
    Rhamnaceae: '🪢', // Buckthorn family - "Tying knots in nature."
    Elaeagnaceae: '🌾', // Oleaster family - "Silver linings in every leaf."
    Cannabaceae: '🌿', // Hemp family - "High on life."
    Droseraceae: '🪰', // Sundew family - "Bug-eating champions."
    Nepenthaceae: '🪤', // Tropical pitcher plant family - "Nature's fly traps."
    Passifloraceae: '💫', // Passionflower family - "Out of this world."
    Begoniaceae: '🎨', // Begonia family - "Painting the garden with color."
    Juglandaceae: '🥜', // Walnut family - "Cracking the nutty mysteries."
    Casuarinaceae: '🎋', // She-oak family - "Whispering in the wind."
    Urticaceae: '🩹', // Nettle family - "Ouch! Handle with care."
    Adoxaceae: '🎻', // Moschatel family - "Playing the symphony of spring."
    Goodeniaceae: '🌊', // Goodenia family - "Riding the waves of beauty."
    Menyanthaceae: '🦢', // Buckbean family - "Graceful as a swan."
    Polygalaceae: '🧙‍♂️', // Milkwort family - "Magical milk makers."
    Simaroubaceae: '🪵', // Quassia family - "Wood you believe it?"
    Pittosporaceae: '🍬', // Pittosporum family - "Sticky seeds, sweet vibes."
    Phyllanthaceae: '🧃', // Leaf-flower family - "Juicy secrets in every leaf."
    Balsaminaceae: '💥', // Balsam family - "Exploding seeds like drama queens."
    Cleomaceae: '🎭', // Spider flower family - "Masked performers of the garden."
    Tropaeolaceae: '🥗', // Nasturtium family - "Salads never looked so good."
    Linaceae: '📜', // Flax family - "Paper-thin but tough as nails."
    Altingiaceae: '🍁', // Sweetgum family - "Spiky balls, sweet scent."
    Platanaceae: '🌳', // Plane tree family - "Bark that peels with style."
    Hamamelidaceae: '🧙‍♀️', // Witch hazel family - "Witchy blossoms in winter."
    Nyssaceae: '📸', // Tupelo family - "Photogenic trees for swamp shoots."
    Tamaricaceae: '🏜️', // Tamarisk family - "Thriving in the dry drama."
    Frankeniaceae: '🧂', // Frankenia family - "Salty souls of the shoreline."
    Polemoniaceae: '🎨', // Phlox family - "Color palette professionals."
    Hydrangeaceae: '🎭', // Hydrangea family - "Color-changing garden stars."
    Santalaceae: '💸', // Sandalwood family - "Smells like luxury."
    Buxaceae: '✂️', // Boxwood family - "Topiary artists' favorite."
    Theaceae: '🍵', // Tea family - "Steeped in tradition."
    Lecythidaceae: '🎇', // Brazil nut family - "Nuts with fireworks inside."
    Tiliaceae: '🍯', // Linden family - "Buzzing with bee-love."
    Dillenniaceae: '🎁', // Dillenia family - "Tough shells, sweet surprises."
    Clusiaceae: '🧴', // Garcinia family - "Butter, balm, and beauty."
    Pandanaceae: '🍰', // Pandan family - "Flavor of tropical dreams."
    Dichapetalaceae: '☠️', // Dichapetalum family - "Pretty but deadly."
    Gunneraceae: '🎩', // Gunnera family - "Oversized leaves, Victorian drama."
    Myristicaceae: '🫚', // Nutmeg family - "Spicing things up since forever."
    Annonaceae: '🍮', // Custard apple family - "Dessert disguised as fruit."
    Monimiaceae: '🌫️', // Monimia family - "Mysterious as morning fog."
    Calycanthaceae: '🧴', // Sweetshrub family - "Fragrance in full bloom."
    Hydrophyllaceae: '💧', // Waterleaf family - "Thirsty for attention."
    Tectariaceae: '🌀', // Fern family - "Coiling into the fern dimension."
    Blechnaceae: '🌿', // Chain fern family - "Ferns with serious structure."
    Dennstaedtiaceae: '🦖', // Bracken family - "Dinosaurs' favorite snack?"
    Osmundaceae: '🛁', // Royal fern family - "Royal soak in the wetlands."
    Equisetaceae: '📏', // Horsetail family - "Measuring up to ancient times."
    Liliaceae: '🌷', // Lily family - "Elegant and timeless."
    Tulipaceae: '🌷', // Tulip family - "Spring's favorite bloom."
    Pteridaceae: '🌿', // Fern family - "Ferns: the ancient green."
    default: '❓' // Default icon for unknown - "Who knows? Not me!"
};

export { 
    MAXSIZE_GARDEN, 
    PAGES, 
    COLORS, 
    ICONS, 
    MAX_PLANTS_NOTIFICATION, 
    MAX_CHAR_NOTIFICATION,
    MAX_RESPONSE_PLANTS
};