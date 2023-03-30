import PipelineTitle from "src/component/PipelineTitle";

const NameTag = (props: {
    children: React.ReactNode;
}) => {
    const { children } = props;

    return <span style={{ maxWidth: '50px' }}>
        <PipelineTitle variant={'small'} >
            {children}
        </PipelineTitle>
    </span>;
}

export default NameTag;
