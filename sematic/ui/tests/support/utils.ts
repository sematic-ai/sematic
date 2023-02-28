import run from '../fixtures/run';

export function createRun(props: Partial<typeof run> = {}) {
    return {
        ...run,
        ...props
    };
}