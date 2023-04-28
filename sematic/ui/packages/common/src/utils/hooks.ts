import { useRef } from 'react';

export function useRefFn<T>(initializer: () => T): T {
    const instanceRef = useRef<T | null>(null)

    function getInstance() {
        let instance = instanceRef.current;
        if (instance !== null) {
            return instance;
        }
        // Lazy init
        let newInstance = initializer();
        instanceRef.current = newInstance;
        return newInstance;
    } 

    return getInstance();
}
