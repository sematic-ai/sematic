import TagsList from "src/component/TagsList";

interface TagsColumnProps {
    tags: string[];
}

export const TagsColumn = (props: TagsColumnProps) => {
    const { tags } = props;

    if (tags.length === 0) {
        return null;
    }

    return <TagsList tags={tags} />
}

export default TagsColumn;
