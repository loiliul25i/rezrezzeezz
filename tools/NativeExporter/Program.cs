using CodeWalker.GameFiles;
using System.Xml;

if (args.Length != 2)
    throw new ArgumentException("Usage: NativeExporter <sources/cwxml> <hw_weapons/stream>");
var source = Path.GetFullPath(args[0]);
var destination = Path.GetFullPath(args[1]);
Directory.CreateDirectory(destination);
RpfManager.IsGen9 = false; // FiveM GTA V Legacy, version 165 YDR and version 13 YTD.
int drawables = 0;
foreach (var input in Directory.GetFiles(source, "*.ydr.xml").Order())
{
    var name = Path.GetFileName(input).Replace(".ydr.xml", "");
    var originalXml = File.ReadAllText(input);
    var drawable = XmlYdr.GetYdr(originalXml, Path.Combine(source, name));
    var bytes = drawable.Save();
    if (System.Text.Encoding.ASCII.GetString(bytes, 0, 4) != "RSC7")
        throw new Exception("Not a native RSC7 resource: " + name);
    var check = new YdrFile();
    check.Load(bytes);
    if (check.Drawable?.DrawableModels?.High == null || check.Drawable.DrawableModels.High.Length == 0)
        throw new Exception("Failed to decode geometry: " + name);
    var roundtrip = YdrXml.GetXml(check);
    var before = new XmlDocument(); before.LoadXml(originalXml);
    var after = new XmlDocument(); after.LoadXml(roundtrip);
    foreach (var xpath in new[] { "//Geometries/Item", "//Skeleton/Bones/Item", "//Shaders/Item" })
        if (before.SelectNodes(xpath)!.Count != after.SelectNodes(xpath)!.Count)
            throw new Exception("Roundtrip structure mismatch " + xpath + ": " + name);
    foreach (XmlElement vb in after.SelectNodes("//VertexBuffer/Data")!)
        if (string.IsNullOrWhiteSpace(vb.InnerText))
            throw new Exception("Empty decoded vertex buffer: " + name);
    File.WriteAllBytes(Path.Combine(destination, name + ".ydr"), bytes);
    var validation = Path.Combine(source, "..", "native_validation");
    Directory.CreateDirectory(validation);
    File.WriteAllText(Path.Combine(validation, name + ".roundtrip.xml"), roundtrip);
    Console.WriteLine($"PASS {name}.ydr: {bytes.Length} bytes, native decode / geometry / shaders / skeleton verified");
    drawables++;
}
foreach (var input in Directory.GetFiles(source, "*.ytd.xml"))
{
    var name = Path.GetFileName(input).Replace(".ytd.xml", "");
    var texture = XmlYtd.GetYtd(File.ReadAllText(input), Path.Combine(source, name));
    var bytes = texture.Save();
    var check = new YtdFile(); check.Load(bytes);
    if (check.TextureDict?.Textures?.data_items?.Length != 1)
        throw new Exception("Texture dictionary failed native roundtrip");
    var atlas = check.TextureDict.Textures.data_items[0];
    if (atlas.Width != 1024 || atlas.Height != 512 || atlas.Levels != 11)
        throw new Exception("Decoded atlas dimensions or mip levels mismatch");
    File.WriteAllBytes(Path.Combine(destination, name + ".ytd"), bytes);
    Console.WriteLine($"PASS {name}.ytd: {bytes.Length} bytes, native texture dictionary decode verified");
}
if (drawables != 8) throw new Exception($"Expected five weapons and three magazines, got {drawables}");
