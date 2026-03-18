use crate::{NUM_SPACES_PER_VIAL, core::Color};

/// Represents a 0-based index retrieving a vial from all vials
pub type VialIndex = u8;
/// Represents a 0-based index into a single vial
pub type SpaceIndex = u8;

/// The size to use when storing game and other numbers of comparable size
pub type DepthSize = u8;

/// A vial is a column containing colored liquids, represented as characters
/// Each vial has exactly NUM_SPACES_PER_VIAL spaces
pub type Vial = [Color; NUM_SPACES_PER_VIAL];
