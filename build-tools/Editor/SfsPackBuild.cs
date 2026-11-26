// Noninteractive counterpart to the official toolkit's SFS/Build Pack window.
// Copied into the prepared Unity project's Assets/Editor by scripts/ci/build_pack.py.
using System;
using System.IO;
using System.Linq;
using System.Text;
using ModLoader;
using UnityEditor;
using UnityEngine;

namespace SfsElectricity.CI
{
    public static class PackBuilder
    {
        const string BundleName = "n2o4s_electricity";
        const string AssetRoot = "Assets/Resources/Electricity/";

        // Each platform runs in a separate Unity process with -buildTarget set.
        public static void BuildPlatform()
        {
            int errors = 0;
            Application.logMessageReceived += CountErrors;
            void CountErrors(string message, string stack, LogType type)
            {
                if (type == LogType.Error || type == LogType.Exception || type == LogType.Assert)
                    errors++;
            }

            try
            {
                string field = Argument("-sfsPlatform");
                string output = Path.GetFullPath(Argument("-sfsBundleOutput"));
                BuildTarget target = field switch
                {
                    "WindowsBuild" => BuildTarget.StandaloneWindows64,
                    "MacBuild" => BuildTarget.StandaloneOSX,
                    "AndroidBuild" => BuildTarget.Android,
                    "IOS_Build" => BuildTarget.iOS,
                    _ => throw new ArgumentException("Unknown pack platform: " + field)
                };
                if (Application.unityVersion != "6000.1.17f1")
                    throw new InvalidOperationException("Expected Unity 6000.1.17f1; got " + Application.unityVersion);
                if (!BuildPipeline.IsBuildTargetSupported(BuildPipeline.GetBuildTargetGroup(target), target))
                    throw new InvalidOperationException("Install Unity build support for " + target);
                if (EditorUserBuildSettings.activeBuildTarget != target)
                    throw new InvalidOperationException("Launch Unity with the matching -buildTarget for " + target);

                AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
                string[] paths = AssetDatabase.GetAssetPathsFromAssetBundle(BundleName);
                string[] required =
                {
                    AssetRoot + "Scriptables/PackData.asset",
                    AssetRoot + "Parts/Ion Drive.prefab",
                    AssetRoot + "Parts/Electric RCS Thruster.prefab"
                };
                if (paths.Length == 0 || paths.Any(p => !p.StartsWith(AssetRoot, StringComparison.Ordinal)))
                    throw new InvalidOperationException("Pack label is empty or includes assets outside Electricity.");
                if (required.Any(p => !paths.Contains(p)))
                    throw new InvalidOperationException("PackData, Ion Drive, or Electric RCS is not bundle-labeled.");
                PackData data = AssetDatabase.LoadAssetAtPath<PackData>(required[0]);
                if (data == null || string.IsNullOrWhiteSpace(data.DisplayName) || string.IsNullOrWhiteSpace(data.Version))
                    throw new InvalidOperationException("PackData is missing or invalid.");

                foreach (string path in paths.Where(p => p.EndsWith(".prefab", StringComparison.Ordinal)))
                {
                    GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                    if (prefab == null)
                        throw new InvalidOperationException("Cannot import prefab: " + path);
                    foreach (Transform child in prefab.GetComponentsInChildren<Transform>(true))
                        if (GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(child.gameObject) != 0)
                            throw new InvalidOperationException("Missing script in " + path + ": " + child.name);
                }

                Directory.CreateDirectory(output);
                var build = new AssetBundleBuild
                {
                    assetBundleName = BundleName,
                    assetNames = paths.OrderBy(p => p, StringComparer.Ordinal).ToArray()
                };
                AssetBundleManifest manifest = BuildPipeline.BuildAssetBundles(output, new[] { build },
                    BuildAssetBundleOptions.StrictMode | BuildAssetBundleOptions.ForceRebuildAssetBundle, target);
                if (manifest == null || errors != 0)
                    throw new InvalidOperationException("AssetBundle build failed; inspect the complete Unity log.");
                if (manifest.GetAllDependencies(BundleName).Length != 0)
                    throw new InvalidOperationException("Bundle requires sibling bundles not included in the .pack.");
                string bundle = Path.Combine(output, BundleName);
                if (!File.Exists(bundle) || new FileInfo(bundle).Length < 8)
                    throw new InvalidOperationException("No nonempty bundle was produced.");
                using (var stream = File.OpenRead(bundle))
                {
                    byte[] signature = new byte[8];
                    if (stream.Read(signature, 0, signature.Length) != signature.Length ||
                        Encoding.ASCII.GetString(signature) != "UnityFS\0")
                        throw new InvalidOperationException("Expected a UnityFS AssetBundle.");
                }
                Debug.Log("SFS_PACK_PLATFORM_OK " + field);
                EditorApplication.Exit(0);
            }
            catch (Exception exception)
            {
                Debug.LogException(exception);
                EditorApplication.Exit(1);
            }
            finally
            {
                Application.logMessageReceived -= CountErrors;
            }
        }

        static string Argument(string name)
        {
            string[] args = Environment.GetCommandLineArgs();
            int index = Array.IndexOf(args, name);
            if (index < 0 || index + 1 >= args.Length || string.IsNullOrWhiteSpace(args[index + 1]))
                throw new ArgumentException("Missing argument " + name);
            return args[index + 1];
        }
    }
}
