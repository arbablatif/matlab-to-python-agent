function export_reference(script_path, out_path, varnames)
% EXPORT_REFERENCE  Run a MATLAB sample script and save selected workspace
% variables to JSON. These files are the "ground truth" the converted
% Python must reproduce.
%   export_reference('samples/fft_analysis.m', 'samples/references/fft_analysis.json', {'P1','f'})
    [script_dir, ~, ~] = fileparts(script_path);
    old = cd(script_dir);                 % so saveas() etc. write next to the script
    cleanup = onCleanup(@() cd(old));
    run(script_path);                      % variables land in this function's workspace
    s = struct();
    for i = 1:numel(varnames)
        s.(varnames{i}) = eval(varnames{i});
    end
    s.x__matlab_version = version;         % provenance
    fid = fopen(out_path, 'w');
    fprintf(fid, '%s', jsonencode(s, 'PrettyPrint', true));
    fclose(fid);
    close all;
end
