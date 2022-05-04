import GlowChipColors from "../components/GlowChip/GlowChipColors";

function UniqueColorAssigner(listOfArraysToAssign: any) {
    if (listOfArraysToAssign.length <= 0 ) return {};

    let mergedValues = [];
    for (let values of listOfArraysToAssign) {
        mergedValues.push(...values);
    }

    // Merge arrays and remove dupes
    const uniqueValues = [...new Set(mergedValues)];

    // Key-value hash map that stores the string value along with the unique color assigned
    let colorHash = new Object();

    uniqueValues.map((value, index) => {
        const colorObject = GlowChipColors[index % GlowChipColors.length];
        colorHash[value] = {
            value,
            color: colorObject.hexCode,
            colorName: colorObject.name,
        };
    });

    return colorHash;
}

export default UniqueColorAssigner;